from src.core.types import PlayerState


def route(state: PlayerState):
    if state["input"].request:
        return "use_ability"
    return "idle"
