from src.core.types import GMGraphState


def gm_refine_node(state: GMGraphState) -> GMGraphState:
    """
    GM コメントを再生成（refine）するための準備ノード。

    責務:
    - 直前のレビュー結果を internal に保存
    - 次の gm_generate が「修正付き生成」をできるようにする
    - world_state には一切触れない
    """
    internal = state["internal"]

    review = internal.last_gm_review

    # レビューがなければ何もしない
    if review is None:
        return state

    # generate 側で参照できるようにする
    internal.gm_refine_instruction = review.reason
    internal.refine_count += 1

    return state
