from src.core.types import PlayerState, RoleProb
from src.game.player.belief_generator import believe_generator
from src.core.roles import get_all_role_names


def belief_update_node(state: PlayerState) -> PlayerState:
    """
    蓄積された観測イベントから belief を更新するノード。

    責務:
    - memory.observed_events から未処理のイベントを取得
    - BeliefGenerator を使用して belief を更新
    - 発言者として指名されたタイミング（strategy_generate の前）で実行

    設計意図:
    - interpret_speech では発言を観測イベントとして記録するのみ
    - このノードで、自分が発言するタイミングで belief を一括更新
    - これにより LLM 呼び出しを削減し、責務を明確に分離
    """
    memory = state["memory"]

    # 未処理の speak イベントを取得
    unprocessed_events = [
        e for e in memory.observed_events
        if e.event_type == "speak"
    ]

    if not unprocessed_events:
        print("[belief_update_node] No unprocessed speak events, skipping belief update")
        return state

    print(f"[belief_update_node] Updating beliefs based on {len(unprocessed_events)} observed events")

    # 最新の観測イベントを使って belief を更新
    # （複数イベントがある場合は最新のものをコンテキストとして渡す）
    latest_event = unprocessed_events[-1]

    new_beliefs = believe_generator.generate(
        memory=memory,
        observed=latest_event,
    )

    if new_beliefs is not None:
        # 自分自身の役職は固定（安全装置）
        # LLM が自分自身を含めなかった場合に備え、安全にロールリストを取得
        if memory.self_name in new_beliefs:
            available_roles = list(new_beliefs[memory.self_name].probs.keys())
        elif new_beliefs:
            # 他のプレイヤーから役職リストを取得
            available_roles = list(next(iter(new_beliefs.values())).probs.keys())
        else:
            # フォールバック: デフォルトの役職リスト
            available_roles = get_all_role_names()
        
        self_probs = {
            role: (1.0 if role == memory.self_role else 0.0)
            for role in available_roles
        }
        new_beliefs[memory.self_name] = RoleProb(probs=self_probs)
        memory.role_beliefs = new_beliefs
        print("[belief_update_node] Beliefs updated successfully")
    else:
        print("[belief_update_node] Failed to update beliefs (LLM returned None)")

    return state
