from src.game.reflection.generator import reflection_generator
from src.core.types import PlayerState


def reflection_node(state: PlayerState) -> PlayerState:
    event = state["input"].event
    request = state["input"].request
    memory = state["memory"]

    print("reflection_node")

    if event is not None:
        reflection = reflection_generator.generate(
            memory=memory,
            observed=event,
        )
        if reflection is not None:
            memory.history.append(reflection)

    if request is not None:
        reflection = reflection_generator.generate(
            memory=memory,
            observed=request,
        )
        if reflection is not None:
            memory.history.append(reflection)

    return state
