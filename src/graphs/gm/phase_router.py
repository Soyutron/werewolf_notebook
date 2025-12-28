from src.core.types import GMGraphState


def phase_router(state: GMGraphState) -> str:
    return state["world_state"].phase
