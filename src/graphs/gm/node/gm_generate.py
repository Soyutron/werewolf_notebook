from src.core.types import GMGraphState
from src.game.gm.gm_comment_generator import gm_comment_generator


def gm_generate_node(state: GMGraphState) -> GMGraphState:
    """
    GM コメントを生成するノード。

    責務:
    - 公開イベント＋未処理イベントを文脈として GM コメントを生成
    - 生成結果を decision.events に追加する
    - フェーズ遷移や成熟判定は行わない
    """

    world = state["world_state"]
    internal = state["internal"]

    # GM が観測できる文脈
    context = world.public_events + world.pending_events
    players = world.players

    gm_comment = gm_comment_generator.generate(
        public_events=context,
        players=players,
        log_summary=internal.log_summary,
        progression_plan=internal.progression_plan,
    )

    # 生成に失敗した場合は何もしない
    if gm_comment is None:
        return state

    internal.pending_gm_comment = gm_comment

    return state
