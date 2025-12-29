"""
PhaseRunner - フェーズごとの進行ロジックを管理するクラス

責務:
- 夜/昼/投票/結果フェーズの進行手順の定義
- run_gm_step() + dispatch() の組み合わせ呼び出し

重要:
- state を直接更新しない
- session のメソッドを呼び出す形で委譲

設計上の位置づけ:
- GameSession から「フェーズ進行の知識」を分離することで、
  新しいフェーズ追加時の変更箇所を明確化する
- session を引数として受け取ることで、
  state の唯一所有者が GameSession である原則を維持する
"""

from __future__ import annotations
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from src.core.session.game_session import GameSession


class PhaseRunner:
    """
    フェーズごとの進行ロジックを管理するクラス。

    責務:
    - 夜/昼/投票/結果フェーズの進行手順の定義
    - run_gm_step() + dispatch() の組み合わせ呼び出し

    重要:
    - state を直接更新しない
    - session のメソッドを呼び出す形で委譲
    """

    def run_night_phase(self, session: "GameSession") -> None:
        """
        夜フェーズを実行する。

        処理内容:
        1. GMGraph を 1 ステップ実行して decision を取得
        2. decision を dispatch して state に反映
        3. フェーズを day に遷移（夜フェーズ固有の完了処理）
        """
        # --- 夜フェーズの進行を 1 ステップ実行 ---
        # 現在の world_state を元に GMGraph を実行し、
        # 夜フェーズで発生すべき「判断結果（decision）」を生成させる
        gm_graph_state = session.run_gm_step()

        # --- GM の判断結果を実行フェーズに反映 ---
        # ・events  : 全プレイヤーに共有される出来事（記憶・推論用）
        # ・requests: 特定プレイヤーへの行動要求
        # Session が state の所有者として、副作用を伴う処理をここで確定させる
        session.dispatch(gm_graph_state["decision"])

    def run_day_step(self, session: "GameSession") -> None:
        """
        昼フェーズ（議論フェーズ）の 1 ステップを実行する。

        このメソッドの責務:
        - 現在の WorldState を元に GMGraph を 1 回だけ実行する
        - GMGraph が返した GameDecision を dispatch して確定反映する

        設計上の重要な前提:
        - このメソッドは world_state.phase == "day" のときのみ呼ばれる
          （フェーズ判定・制御は呼び出し元の責務）
        - フェーズ遷移（day -> vote など）は GMGraph が
          decision.next_phase に意思として示し、
          実際の更新は dispatch が行う
        - ここではループや待機は行わず、
          常に「1 step = 1 decision」とする

        将来拡張:
        - AI 同士の自動進行では外側でループさせる
        - 人間参加（Web / API）の場合は、
          発言イベントなどを追加した後に 1 回だけ呼び出す
        """
        gm_graph_state = session.run_gm_step()
        session.dispatch(gm_graph_state["decision"])

    def run_vote_step(self, session: "GameSession") -> None:
        """
        投票フェーズ（vote フェーズ）の 1 ステップを実行する。

        このメソッドの責務:
        - 現在の WorldState を元に GMGraph を 1 回だけ実行する
        - GMGraph が返した GameDecision を dispatch して確定反映する

        設計上の重要な前提:
        - このメソッドは world_state.phase == "vote" のときのみ呼ばれる
        （フェーズ判定・制御は呼び出し元の責務）
        - フェーズ遷移（vote -> result / end など）は GMGraph が
        decision.next_phase に意思として示し、
        実際の更新は dispatch が行う
        - ここではループや待機は行わず、
        常に「1 step = 1 decision」とする

        将来拡張:
        - 人間プレイヤーが投票を入力した後に 1 回だけ呼び出す
        - AI 同士の自動進行では外側でループ制御する
        """
        gm_graph_state = session.run_gm_step()
        session.dispatch(gm_graph_state["decision"])

    def run_result_step(self, session: "GameSession") -> None:
        """
        結果フェーズ（result フェーズ）の 1 ステップを実行する。

        このメソッドの責務:
        - GMGraph を 1 回だけ実行し、
          勝敗確定・役職公開（reveal）を行う
        - GameDecision を dispatch して最終状態を確定させる

        設計上の前提:
        - world_state.phase == "result" のときのみ呼ばれる
        - result フェーズでは request は一切発生しない
        - decision.next_phase は None（ゲーム終了）
        """
        gm_graph_state = session.run_gm_step()
        session.dispatch(gm_graph_state["decision"])
