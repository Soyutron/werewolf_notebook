from src.core.types import PlayerState


def handle_interpret_speech(state: PlayerState) -> PlayerState:
    """
    発言（speak）を受け取り、観測イベントとして保存するノード。

    責務:
    - 発言イベントを observed_events に記録する
    - belief の更新は行わない（belief_update_node で実行）
    - 行動はしない（output = None）
    """
    event = state["input"].event
    memory = state["memory"]

    # speak イベント以外は無視
    if event is None or event.event_type != "speak":
        state["output"] = None
        return state

    # 観測イベントとして保存（belief 更新は belief_update_node で行う）
    memory.observed_events.append(event)

    state["output"] = None
    return state
