from src.core.types import PlayerState


def handle_vote_started(state: PlayerState) -> PlayerState:
    """
    投票が始まったことを受け取り、状態を更新するだけのノード。
    """
    event = state["input"].event
    memory = state["memory"]
    memory.observed_events.append(event)

    # 行動はしない
    state["output"] = None
    return state
