# src/game/gm/nodes/gm_refine.py

from src.core.types import GMGraphState
from src.game.gm.gm_comment_refiner import gm_comment_refiner


def gm_refine_node(state: GMGraphState) -> GMGraphState:
    """
    GM コメントをレビュー指摘を踏まえて再生成するノード。

    責務:
    - public_events + pending_events を文脈として使用
    - 直前の GMReview（internal.last_gm_review）を必ず反映する
    - 再生成したコメントを internal.pending_gm_comment に上書きする
    - commit / 判定 / フェーズ遷移は行わない
    """
    print("gm_refine_node")

    world = state["world_state"]
    internal = state["internal"]

    # レビューが存在しない場合は何もしない（安全装置）
    if internal.last_gm_review is None:
        return state

    # GM が観測できる文脈
    context = world.public_events + world.pending_events
    players = world.players

    gm_comment = gm_comment_refiner.refine(
        original=internal.pending_gm_comment,
        review=internal.last_gm_review,
        public_events=context,
        players=players,
    )

    # 再生成に失敗した場合は state をそのまま返す
    if gm_comment is None:
        return state

    # pending を上書き（refine なので過去案は捨てる）
    internal.pending_gm_comment = gm_comment

    return state
