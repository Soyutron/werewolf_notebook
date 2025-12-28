from src.graphs.gm.state import GMGraphState


def phase_router(state: GMGraphState) -> str:
    return state["world_state"].phase
