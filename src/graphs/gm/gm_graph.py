from src.core.types import (
    GameDecision,
    GMGraphState,
    PlayerRequest,
    GameEvent,
)
from typing import Protocol


class GMGraph(Protocol):
    """
    GM（進行役）の思考エンジンの共通インターフェース。

    - ゲーム全体の進行判断を担当する
    - WorldState を読み取り、次に起こすべき意思決定を GameDecision にまとめる
    - LangGraph / Dummy / Test 実装を差し替え可能にするため Protocol で定義
    """

    def invoke(self, state: GMGraphState) -> GMGraphState:
        """
        GMGraph のメインエントリポイント。

        Parameters
        ----------
        state : GMGraphState
            - world_state : 現在の公開ゲーム状態（事実）
            - decision    : このステップで生成する判断結果

        Returns
        -------
        GMGraphState
            world_state は基本的に変更せず、
            decision のみを更新して返すことを想定する
        """
        ...


class DummyGMGraph:
    """
    仮実装の GMGraph。

    - 設計検証・疎通確認用
    - 実際の推論や分岐ロジックは持たない
    - 現在のフェーズに応じた最低限の GameDecision を生成する
    """

    def invoke(self, state: GMGraphState) -> GMGraphState:
        # --- 公開状態（事実）を取得 ---
        # GMGraph は world_state を「読む」ことが主で、
        # 原則として直接変更しない
        world_state = state["world_state"]
        phase = world_state.phase

        # --- このステップで生成する意思決定 ---
        decision = GameDecision()
        internal = state["internal"]

        # =========================
        # 夜フェーズ
        # =========================
        if phase == "night":
            # フェーズ開始イベント（全員に共有される事実）
            decision.events.append(
                GameEvent(
                    event_type="phase_start",
                    payload={"phase": "night"},
                )
            )

            # 各プレイヤーに夜行動のリクエストを送る
            # （ここでは全員が能力を使える前提のダミー実装）
            decision.requests = {
                player: PlayerRequest(
                    request_type="use_ability",
                    payload={
                        # 自分以外のプレイヤーを候補として提示
                        "candidates": [p for p in world_state.players if p != player]
                    },
                )
                for player in world_state.players
            }

            # 夜はプレイヤーの応答待ちなのでフェーズは進めない
            decision.next_phase = None

        # =========================
        # 昼フェーズ
        # =========================
        elif phase == "day":
            # デバッグ用ログ
            print("昼フェーズ")

            # 議論・投票などがまだ続く想定
            decision.next_phase = "vote"

        # =========================
        # 投票フェーズ
        # =========================
        elif phase == "vote":
            # デバッグ用ログ
            print("投票フェーズ")

            # 議論・投票などがまだ続く想定
            decision.next_phase = "result"

        # =========================
        # 結果フェーズ
        # =========================
        elif phase == "result":
            # デバッグ用ログ
            print("結果フェーズ")

            # 明示的にフェーズが終わった場合は結果公開へ
            decision.next_phase = None

        # --- GMGraphState を組み立てて返却 ---
        return GMGraphState(
            world_state=world_state,  # immutable な事実状態
            decision=decision,  # このステップの判断結果
            internal=internal,  # このステップの内部進行状態
        )


# 仮の GMGraph 実体
# GameSession などから注入して使用する
gm_graph = DummyGMGraph()
