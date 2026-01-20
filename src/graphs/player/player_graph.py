from src.core.types.player import PlayerState, PlayerOutput
from typing import Protocol
from langgraph.graph import StateGraph, START, END
from src.graphs.player.observe_event.night_started import handle_night_started
from src.graphs.player.handle_request.use_ability import handle_use_ability
from src.graphs.player.observe_event.gm_comment import handle_gm_comment
from src.graphs.player.observe_event.divine_result import handle_divine_result
from src.graphs.player.observe_event.day_started import handle_day_started
from src.graphs.player.observe_event.vote_started import handle_vote_started
from src.graphs.player.observe_event.interpret_speech import handle_interpret_speech
from src.graphs.player.observe_event.role_swapped import handle_role_swapped
from src.graphs.player.node.reflection_node import reflection_node
from src.graphs.player.node.reaction_node import reaction_node
from src.graphs.player.phase_router import phase_router
from src.graphs.player.handle_request.vote import handle_vote
from src.graphs.player.post_reflection_action_router import (
    post_reflection_action_router,
)


class PlayerGraph(Protocol):
    """
    Player の思考エンジンの共通インターフェース。

    - プレイヤーが「与えられた入力（PlayerInput）」に対して
      どのような行動（PlayerOutput）を返すかを決定する責務を持つ
    - LangGraph 実装 / ダミー実装 / テスト用スタブなどを
      差し替え可能にするため Protocol として定義している
    - state は GameSession が所有し、PlayerGraph は
      「受け取って → 更新して → 返す」だけの純粋な計算単位
    """

    def invoke(self, state: PlayerState) -> PlayerState:
        """
        与えられた PlayerState を入力として受け取り、
        次の PlayerState を返す。

        - state の中身（memory / input / output）をどこまで
          変更するかは PlayerGraph の実装に委ねられる
        - 副作用（DB 書き込みなど）は持たない想定
        """
        ...


class LangGraphPlayerAdapter:
    def __init__(self, graph):
        self.graph = graph

    def invoke(self, state: PlayerState) -> PlayerState:
        return self.graph.invoke(state)


def build_player_graph():
    # Lazy imports to avoid circular import chain
    # (player_graph -> nodes -> game components -> core.__init__ -> session -> controller -> player_graph)
    from src.graphs.player.node.strategy_generate import strategy_generate_node
    from src.graphs.player.node.strategy_plan_generate import strategy_plan_generate_node
    from src.graphs.player.node.speak_generate import speak_generate_node
    from src.graphs.player.node.speak_review_router import speak_review_router_node
    from src.graphs.player.node.speak_refine import speak_refine_node
    from src.graphs.player.node.speak_commit import speak_commit_node
    from src.graphs.player.node.belief_update_node import belief_update_node
    from src.graphs.player.node.log_summarize_node import log_summarize_node

    graph = StateGraph(PlayerState)

    # === 既存のノード ===
    graph.add_node("night_started", handle_night_started)
    graph.add_node("use_ability", handle_use_ability)
    graph.add_node("divine_result", handle_divine_result)
    graph.add_node("day_started", handle_day_started)
    graph.add_node("gm_comment", handle_gm_comment)
    graph.add_node("interpret_speech", handle_interpret_speech)
    graph.add_node("vote_started", handle_vote_started)
    graph.add_node("vote", handle_vote)
    graph.add_node("role_swapped", handle_role_swapped)
    graph.add_node("reflection", reflection_node)
    graph.add_node("reaction", reaction_node)

    # === 戦略→発言フローのノード ===
    graph.add_node("strategy_plan_generate", strategy_plan_generate_node)
    graph.add_node("belief_update", belief_update_node)
    graph.add_node("log_summarize", log_summarize_node)
    graph.add_node("strategy_generate", strategy_generate_node)
    graph.add_node("speak_generate", speak_generate_node)
    graph.add_node("speak_refine", speak_refine_node)
    graph.add_node("speak_commit", speak_commit_node)

    # === 既存のエッジ（END へ直接接続するもの）===
    # graph.add_edge("night_started", END)  <-- Changed to go to strategy_plan_generate
    graph.add_edge("strategy_plan_generate", END)
    # graph.add_edge("day_started", END)  <-- Changed to go to strategy_plan_generate
    graph.add_edge("vote_started", END)
    graph.add_edge("use_ability", END)
    graph.add_edge("divine_result", END)
    graph.add_edge("gm_comment", END)
    graph.add_edge("reaction", END)
    graph.add_edge("reflection", END)
    graph.add_edge("interpret_speech", END)
    graph.add_edge("vote", END)
    graph.add_edge("role_swapped", END)

    # === Night Phase Edge ===
    # night_started -> END (夜は行動決定して思考終了、戦略生成はまだしない)
    graph.add_edge("night_started", END)

    # === Day Start Flow ===
    # day_started -> strategy_plan_generate (昼開始時に戦略生成)
    graph.add_edge("day_started", "strategy_plan_generate")

    # === 戦略→発言フローのエッジ ===
    # belief_update → log_summarize → strategy_generate → speak_generate
    graph.add_edge("belief_update", "log_summarize")
    graph.add_edge("log_summarize", "strategy_generate")
    graph.add_edge("strategy_generate", "speak_generate")

    # speak_generate → speak_review_router
    graph.add_edge("speak_generate", "speak_commit")
    # graph.add_conditional_edges(
    #     "speak_generate",
    #     speak_review_router_node,
    #     {
    #         "commit": "speak_commit",  # 発言確定
    #         "refine": "speak_refine",  # 発言修正
    #     },
    # )

    # speak_refine → speak_review_router（ループ）
    graph.add_conditional_edges(
        "speak_refine",
        speak_review_router_node,
        {
            "commit": "speak_commit",
            "refine": "speak_refine",
        },
    )

    # speak_commit → END
    graph.add_edge("speak_commit", END)

    # START から phase に応じて分岐
    graph.add_conditional_edges(START, phase_router)
    graph.add_conditional_edges("reflection", post_reflection_action_router)

    return graph.compile()


class DummyPlayerGraph:
    """
    仮実装の PlayerGraph。

    - input.request が存在する場合:
        request の内容をそのまま PlayerOutput に変換する
    - input.request が存在しない場合:
        「待機ターン」とみなし output は None のまま返す

    設計検証・Session / Controller の動作確認用。
    思考ロジックや戦略判断は一切含まない。
    """

    def invoke(self, state: PlayerState) -> PlayerState:
        # GM から渡された「このターンの入力」を取得
        request = state["input"].request

        # 行動要求がない = 待機ターン
        # memory 等は変更せず、output も生成しない
        if request is None:
            state["output"] = None
            return state

        # 行動要求がある場合は、
        # request の内容をそのまま output に変換するだけ
        # （判断・分岐・推論などは一切行わない）
        state["output"] = PlayerOutput(
            action=request.request_type,
            payload=request.payload,
        )

        # 更新済みの state を返却
        return state


# 仮の PlayerGraph インスタンス
# - Session や Controller に注入して動作確認に使う
# - 後から LangGraph 実装に差し替える前提
# player_graph = DummyPlayerGraph()
player_graph = LangGraphPlayerAdapter(build_player_graph())

