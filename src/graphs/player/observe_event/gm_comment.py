from src.core.types import PlayerState


def handle_gm_comment(state: PlayerState) -> PlayerState:
    """
    GMコメントを受け取り、行動を決定するノード。
    """
    event = state["input"].event
    memory = state["memory"]
    memory.observed_events.append(event)

    # 行動はしない
    state["output"] = None
    return state
