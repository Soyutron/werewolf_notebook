from src.core.types import PlayerState


def handle_speak(state: PlayerState) -> PlayerState:
    """
    話すことを受け取り、話す内容を決定するノード。
    """

    # 行動はしない
    state["output"] = None
    return state
