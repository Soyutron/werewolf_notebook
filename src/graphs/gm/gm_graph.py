from src.core.types import (
    GameDecision,
    GMGraphState,
    PlayerRequest,
    GameEvent,
)
from typing import Protocol
from langgraph.graph import StateGraph, START, END
from src.graphs.gm.node.gm_plan import gm_plan_node

from src.graphs.gm.node.night_phase import night_phase_node
from src.graphs.gm.node.day_phase_entry import day_phase_entry_node
from src.graphs.gm.node.day_phase_router import day_phase_router_node
from src.graphs.gm.node.vote_phase import vote_phase_node
from src.graphs.gm.node.result_phase import result_phase_node
from src.graphs.gm.phase_router import phase_router
from src.graphs.gm.node.gm_generate import gm_generate_node
from src.graphs.gm.node.gm_commit import gm_commit_node
from src.graphs.gm.node.gm_comment_review_router import gm_comment_review_router_node
from src.graphs.gm.node.gm_refine import gm_refine_node
from src.graphs.gm.node.log_summarize_node import gm_log_summarize_node



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


class LangGraphGMAdapter:
    def __init__(self, graph):
        self.graph = graph

    def invoke(self, state: GMGraphState) -> GMGraphState:
        return self.graph.invoke(state)


def build_gm_graph():
    graph = StateGraph(GMGraphState)

    # ノード登録
    # "night" ノードを gm_plan_node に割り当て（入口）
    graph.add_node("night", gm_plan_node)
    # 実際の夜行動処理を "night_action" として登録
    graph.add_node("night_action", night_phase_node)
    
    graph.add_node("day", day_phase_entry_node)
    graph.add_node("log_summarize", gm_log_summarize_node)
    graph.add_node("gm_generate", gm_generate_node)
    graph.add_node("gm_commit", gm_commit_node)
    graph.add_node("gm_refine", gm_refine_node)
    graph.add_node("vote", vote_phase_node)
    graph.add_node("result", result_phase_node)

    # START から phase に応じて分岐
    graph.add_conditional_edges(START, phase_router)
    graph.add_conditional_edges(
        "day",
        day_phase_router_node,
        {
            "continue": "log_summarize",
            "vote": END,
        },
    )
    
    # night (plan) -> night_action (action request)
    graph.add_edge("night", "night_action")
    graph.add_edge("night_action", END)

    # log_summarize → gm_generate
    graph.add_edge("log_summarize", "gm_generate")
    graph.add_edge("gm_generate", "gm_commit")
    # graph.add_conditional_edges(
    #     "gm_generate",
    #     gm_comment_review_router_node,
    #     {
    #         "commit": "gm_commit",
    #         "refine": "gm_refine",
    #     },
    # )
    graph.add_conditional_edges(
        "gm_refine",
        gm_comment_review_router_node,
        {
            "commit": "gm_commit",
            "refine": "gm_refine",
        },
    )

    # 1ノードで終了
    # "night" (gm_plan) -> "night_action" -> END is already defined above
    graph.add_edge("vote", END)
    graph.add_edge("result", END)
    graph.add_edge("gm_commit", END)

    return graph.compile()



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
# gm_graph = DummyGMGraph()
gm_graph = LangGraphGMAdapter(build_gm_graph())
