from src.core.types import PlayerState


def handle_divine_result(state: PlayerState) -> PlayerState:
    """
    占い結果を受け取り、占い師の記憶を更新するノード。

    - divine_result は「占い師本人にのみ」届く
    - 行動は発生しない（output は None）
    """

    event = state["input"].event
    if event is None:
        return state

    if event.event_type != "divine_result":
        return state

    target = event.payload["target"]
    role = event.payload["role"]

    # 記憶更新（例）
    state["memory"].beliefs[target] = role
    if role == "werewolf":
        state["memory"].suspicion[target] = 1
    else:
        state["memory"].suspicion[target] = 0
    state["memory"].observed_events.append(event)

    # 行動はしない
    state["output"] = None
    return state
