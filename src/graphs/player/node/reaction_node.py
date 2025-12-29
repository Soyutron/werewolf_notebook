from src.game.reaction.generator import reaction_generator
from src.core.types import PlayerState


def reaction_node(state: PlayerState) -> PlayerState:
    event = state["input"].event
    request = state["input"].request
    memory = state["memory"]

    if event is not None:
        reaction = reaction_generator.generate(
            memory=memory,
            observed=event,
        )
        if reaction is not None:
            memory.history.append(reaction)

    if request is not None:
        reaction = reaction_generator.generate(
            memory=memory,
            observed=request,
        )
        if reaction is not None:
            memory.history.append(reaction)

    return state
