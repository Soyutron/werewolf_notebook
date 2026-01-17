# src/game/gm/nodes/gm_comment_review_router.py

from src.core.types import GMGraphState
from src.game.gm.gm_comment_reviewer import gm_comment_reviewer

MAX_REVIEW_COUNT = 3


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

    if internal.gm_comment_review_count >= MAX_REVIEW_COUNT:
        return "commit"

    # コメントが存在しない場合は安全側に倒す
    if pending_comment is None:
        return "commit"

    review_events = world.public_events + world.pending_events

    review_result = gm_comment_reviewer.review(
        comment=pending_comment,
        public_events=review_events,
        players=world.players,
    )

    print(review_result)

    internal.last_gm_review = review_result
    internal.gm_comment_review_count += 1

    if review_result.needs_fix:
        return "refine"

    return "commit"
