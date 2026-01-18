"""
Dispatcher - GameDecision を解釈し、ゲーム世界に反映する処理を制御するクラス

責務:
- events の配布制御
- requests の配布制御
- next_phase の更新制御

重要:
- 実際の state 更新は session のコールバック経由
- このクラス自体は state を直接更新しない

設計上の位置づけ:
- GameSession から「判断結果の適用ロジック」を分離することで、
  dispatch 処理の見通しを良くする
- session を引数として受け取ることで、
  state の唯一所有者が GameSession である原則を維持する
"""

from __future__ import annotations
from typing import TYPE_CHECKING
import asyncio

from src.core.types import (
    GameDecision,
    PlayerInput,
)

if TYPE_CHECKING:
    from src.core.session.game_session import GameSession


class Dispatcher:
    """
    GameDecision を解釈し、ゲーム世界に反映する処理を制御するクラス。

    責務:
    - events の配布制御
    - requests の配布制御
    - next_phase の更新制御

    重要:
    - 実際の state 更新は session のコールバック経由
    - このクラス自体は state を直接更新しない
    """

    def dispatch(
        self,
        decision: GameDecision,
        session: "GameSession",
    ) -> None:
        """
        GMGraph から返された GameDecision を受け取り、
        実際のゲーム世界（WorldState / PlayerState）に反映する。

        設計方針:
        - GameDecision は「判断結果」のみを表し、副作用は持たない
        - この dispatch が state を更新する唯一の場所（state の所有者）
        - event と request は同時には来ない運用とする
          （= 観測フェーズと行動フェーズは明確に分離される）
        """
        # =========================================================
        # 1. pending_events の配布（Player 行動の内省）
        # =========================================================
        if session.world_state.pending_events:
            for event in session.world_state.pending_events:
                for player in session.player_states:
                    session.run_player_turn(
                        player=player,
                        input=PlayerInput(event=event),
                    )
            # 配布が終わったら「過去の事実」に昇格
            session.world_state.public_events.extend(session.world_state.pending_events)
            session.world_state.pending_events.clear()

        # =========================================================
        # 2. event の配布（すでに起きた事実の通知）
        # =========================================================
        # - 全プレイヤーに共有される「確定した出来事」
        # - プレイヤーは思考・記憶更新のみを行う（行動はしない）
        # - request と同一 step で同時に存在してよい
        if decision.events:
            # speak イベントとそれ以外を分離
            speak_events = [e for e in decision.events if e.event_type == "speak"]
            other_events = [e for e in decision.events if e.event_type != "speak"]

            # ---------------------------------------------------------
            # 2a. speak 以外のイベント（従来通りの処理）
            # ---------------------------------------------------------
            for event in other_events:
                for player in session.player_states:
                    session.run_player_turn(
                        player=player,
                        input=PlayerInput(event=event),
                    )

            # ---------------------------------------------------------
            # 2b. speak イベント（観測と belief 更新を分離して並列化）
            # ---------------------------------------------------------
            if speak_events:
                # Step 1: 全プレイヤーに観測のみ配布（同期・軽量）
                for event in speak_events:
                    for player in session.player_states:
                        session.observe_event(player=player, event=event)

                # Step 2: belief 更新を並列実行（非同期）
                asyncio.run(session.update_beliefs_async(speak_events))

            # event は全員に配布し終えた後で、
            # 公開ログ（WorldState）として確定させる
            session.world_state.public_events.extend(decision.events)
            # GM がどこまで event を配布し終えたかを示すカーソル
            # （LangGraph 実装や再実行・再開時の安全装置として有用）
            session.gm_internal.gm_event_cursor = len(session.world_state.public_events)

        # =========================================================
        # 2. request の配布（今ターンの行動要求）
        # =========================================================
        # - 特定のプレイヤーにのみ送られる
        # - 実際の行動（発言・投票・夜行動など）を発生させる
        # - event と同一 step で同時に存在してよい
        if decision.requests:
            for player, request in decision.requests.items():
                output = session.run_player_turn(
                    player=player,
                    input=PlayerInput(
                        request=request,
                    ),
                )
                # Player の出力（発言・投票・能力使用など）を
                # GM 視点で解釈・確定させ、世界状態に反映する
                #
                # ここで初めて「行動の結果」が事実になる
                session.resolve_player_output(
                    player=player,
                    output=output,
                )

        # =========================================================
        # 3. フェーズ遷移
        # =========================================================
        # - event / request の処理がすべて完了した後に実行される
        # - フェーズ自体は「進行状態」であり、
        #   event（出来事）とは区別して WorldState に直接反映する
        if decision.next_phase is not None:
            session.world_state.phase = decision.next_phase
