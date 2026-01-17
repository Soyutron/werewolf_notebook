# src/game/gm/nodes/gm_commit_node.py

from src.core.types import GameEvent, GMGraphState, PlayerRequest


def gm_commit_node(state: GMGraphState) -> GMGraphState:
    """
    未確定の GM コメント（pending_gm_comment）を
    正式な GameEvent として確定・公開するノード。

    責務:
    - internal.pending_gm_comment を decision.events に反映する
    - commit 後、pending / review 情報を必ずクリアする
    - world_state やフェーズ制御には一切関与しない
    """

    internal = state["internal"]
    decision = state["decision"]

    pending = internal.pending_gm_comment

    # pending が存在しない場合は何もしない（安全側）
    if pending is None:
        return state

    # GM コメントを GameEvent として確定
    decision.events.append(
        GameEvent(
            event_type="gm_comment",
            payload={
                "speaker": pending.speaker,
                "text": pending.text,
            },
        )
    )

    decision.requests = {
        pending.speaker: PlayerRequest(
            request_type="speak",
            payload={},
        )
    }

    # --- commit 後のクリーンアップ ---
    internal.pending_gm_comment = None
    internal.last_gm_review = None
    internal.gm_comment_review_count = 0

    return state
