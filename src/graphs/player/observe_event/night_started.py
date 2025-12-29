from src.core.types import PlayerState

def handle_night_started(state: PlayerState) -> PlayerState:
    """
    夜が始まったことを受け取り、夜の行動を決定するノード。
    """
    event = state["input"].event
    memory = state["memory"]
    memory.observed_events.append(event)

    # 行動はしない
    state["output"] = None
    return state