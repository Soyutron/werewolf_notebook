from src.core.types import PlayerOutput, PlayerState
from src.game.player.speak_generator import speak_generator


def handle_speak(state: PlayerState) -> PlayerState:
    """
    話すことを受け取り、話す内容を決定するノード。
    """
    print("handle_speak")

    request = state["input"].request
    memory = state["memory"]

    if request is not None:
        speak = speak_generator.generate(
            memory=memory,
            observed=request,
        )
        if speak is not None:
            memory.history.append(speak)

    # 行動はしない
    state["output"] = PlayerOutput(
        action="speak",
        payload={
            "text": speak.text,
        },
    )
    print(state)
    return state
