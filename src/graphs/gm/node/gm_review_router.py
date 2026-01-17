# src/game/gm/nodes/gm_comment_review_router.py

from src.core.types import GMGraphState
from src.game.gm.gm_comment_reviewer import gm_comment_reviewer


def gm_comment_review_router_node(state: GMGraphState) -> str:
    """
    生成された GM コメントをレビューし、
    採用（commit）するか、再生成（refine）するかを判定する Router ノード。

    戻り値:
    - "commit": コメントを確定して公開する
    - "refine": コメントを作り直す
    """

    internal = state["internal"]
    world = state["world_state"]

    pending_comment = internal.pending_gm_comment

    # コメントが存在しない場合は安全側に倒す
    if pending_comment is None:
        return "refine"

    reviewed_comment = gm_comment_reviewer.review(
        comment=pending_comment,
        public_events=world.public_events,
    )

    internal.last_gm_review = reviewed_comment

    if reviewed_comment is None:
        return "refine"

    return "commit"
