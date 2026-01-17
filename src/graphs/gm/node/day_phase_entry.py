# src/game/gm/nodes/day_phase_entry.py

from src.core.types import GameEvent, GMGraphState


def day_phase_entry_node(state: GMGraphState) -> GMGraphState:
    """
    昼フェーズ開始時に一度だけ実行される GM ノード。

    責務:
    - 昼フェーズ開始イベント（day_started）を発火する
    - 二重実行を防ぐため internal.day_started フラグでガードする

    注意:
    - フェーズ遷移の判断は行わない
    - プレイヤー発言や GM コメント生成は行わない
    """

    decision = state["decision"]
    internal = state["internal"]

    # 昼フェーズ開始（1回だけ）
    if not internal.day_started:
        decision.events.append(GameEvent(event_type="day_started", payload={}))
        internal.day_started = True

    return state
