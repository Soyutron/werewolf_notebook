from src.core.types.player import PlayerState


def strategy_plan_generate_node(state: PlayerState) -> PlayerState:
    """
    初期戦略計画（Overall Strategic Plan）を生成するノード。
    夜フェーズ（night_started）の直後に実行されることを想定。

    責務:
    - PlayerMemory.strategy_plan が未設定の場合、StrategyPlanGenerator を用いて生成し保存する。
    - milestone_status を初期化する（固定情報 → 可変情報の導出）。
    """
    # Lazy import
    from src.game.player.strategy_plan_generator import strategy_plan_generator
    from src.game.player.milestone_status_updater import milestone_status_updater

    memory = state["memory"]

    if memory.strategy_plan is None:
        print("[strategy_plan_generate_node] generating initial strategy plan...")
        plan = strategy_plan_generator.generate(memory)
        if plan:
            memory.strategy_plan = plan
            # milestone_status を初期化（固定の milestone_plan から可変の status を導出）
            if plan.milestone_plan and plan.milestone_plan.milestones:
                memory.milestone_status = milestone_status_updater.initialize_status(
                    plan.milestone_plan
                )
                print(f"[strategy_plan_generate_node] Initialized milestone_status with {len(plan.milestone_plan.milestones)} milestones")
        else:
            print("[strategy_plan_generate_node] Failed to generate initial strategy plan")
    else:
        print("[strategy_plan_generate_node] Strategy plan already exists. Skipping.")

    return state
