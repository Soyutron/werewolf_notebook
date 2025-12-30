from src.core.types import PlayerOutput, PlayerState


def handle_speak(state: PlayerState) -> PlayerState:
    """
    話すことを受け取り、話す内容を決定するノード。
    """
    print("handle_speak")

    # 行動はしない
    state["output"] = PlayerOutput(
        action="speak",
        payload=None,
    )
    print(state)
    return state
