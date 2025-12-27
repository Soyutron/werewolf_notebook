from src.core.types import PlayerState


def player_step(state: PlayerState) -> PlayerState:
    input_ = state["input"]

    # event を受け取ったとき
    if "event" in input_:
        state["memory"]["history"].append(input_["event"])

    # request を受け取ったとき
    if "request" in input_:
        req = input_["request"]

        if req["request_type"] == "speak":
            state["output"] = {
                "action": "speak",
                "payload": {"message": "I am villager."},
            }

        elif req["request_type"] == "vote":
            state["output"] = {"action": "vote", "payload": {"target": "Bob"}}

    return state
