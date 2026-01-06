from src.core.types import PlayerState


def post_reflection_action_router(state: PlayerState) -> str:
    """
    reflection 後にどの行動に進むかを決める router。
    """

    if state["input"].request is None:
        return "END"

    action = state["input"].request.request_type

    if action == "speak":
        return "speak"
    if action == "vote":
        return "vote"
    if action == "accuse":
        return "accuse"

    raise ValueError(f"unknown action: {action}")
