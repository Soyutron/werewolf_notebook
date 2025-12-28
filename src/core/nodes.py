from src.core.types import PlayerState, PlayerOutput


def player_step(state: PlayerState) -> PlayerState:
    input_ = state["input"]

    # event を受け取ったとき
    if input_.event is not None:
        state["memory"].history.append(input_.event)

    # request を受け取ったとき
    if input_.request is not None:
        req = input_.request

        if req.request_type == "speak":
            state["output"] = PlayerOutput(
                action="speak",
                payload={"message": "I am villager."},
            )

        elif req.request_type == "vote":
            state["output"] = PlayerOutput(
                action="vote",
                payload={"target": "Bob"},
            )

    return state
