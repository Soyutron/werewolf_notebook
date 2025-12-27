from typing import Callable
from core.types import PlayerState


def make_handle_event(llm) -> Callable[[PlayerState], PlayerState]:
    def handle_event(state: PlayerState) -> PlayerState:
        event = state["input"].get("event")
        if not event:
            return state

        memory = state["memory"]
        memory["history"].append(event)

        if event["type"] == "speech":
            speaker = event["speaker"]
            content = event["content"]

            judgment = llm.evaluate_speech(
                speaker=speaker,
                content=content,
                self_name=memory["self_name"],
                suspicion=memory["suspicion"],
            )

            delta = judgment.get("suspicion_delta")

            if delta == "increase":
                memory["suspicion"][speaker] = (
                    memory["suspicion"].get(speaker, 0.0) + 0.2
                )
            elif delta == "decrease":
                memory["suspicion"][speaker] = max(
                    0.0, memory["suspicion"].get(speaker, 0.0) - 0.2
                )
            else:
                memory["suspicion"].setdefault(speaker, 0.1)

        return state

    return handle_event


def decide_action(state: PlayerState) -> PlayerState:
    request = state["input"].get("request")
    if not request:
        return state

    memory = state["memory"]
    action = request.get("action")

    if action == "speak":
        if memory["suspicion"]:
            target = max(memory["suspicion"], key=memory["suspicion"].get)
            state["output"] = {
                "type": "speech",
                "speaker": memory["self_name"],
                "content": f"I think {target} is suspicious",
            }
        else:
            state["output"] = {
                "type": "speech",
                "speaker": memory["self_name"],
                "content": "I have no information",
            }

    elif action == "vote":
        target = max(memory["suspicion"], key=memory["suspicion"].get)
        state["output"] = {
            "type": "vote",
            "voter": memory["self_name"],
            "target": target,
        }

    return state
