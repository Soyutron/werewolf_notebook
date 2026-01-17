from src.core.types import PlayerState
from src.game.player.belief_generator import believe_generator
from src.core.types import RoleProb


def handle_interpret_speech(state: PlayerState) -> PlayerState:
    """
    発言（speak）を受け取り、belief（role_beliefs）を更新するノード。

    - handle_speak と同じ責務感
    - BeliefGenerator を直接呼ぶ
    - 行動はしない（output = None）
    """
    print("handle_interpret_speech")

    event = state["input"].event
    memory = state["memory"]

    # speak イベント以外は無視
    if event is None or event.event_type != "speak":
        state["output"] = None
        return state

    # 1. 観測イベントとして保存
    memory.observed_events.append(event)

    # 2. belief を更新
    new_beliefs = believe_generator.generate(
        memory=memory,
        observed=event,
    )

    if new_beliefs is not None:
        # 自分自身の役職は固定（安全装置）
        self_probs = {
            role: (1.0 if role == memory.self_role else 0.0)
            for role in new_beliefs[memory.self_name].probs.keys()
        }
        new_beliefs[memory.self_name] = RoleProb(probs=self_probs)

        memory.role_beliefs = new_beliefs

    # 3. 行動はしない
    state["output"] = None
    print(state)
    return state
