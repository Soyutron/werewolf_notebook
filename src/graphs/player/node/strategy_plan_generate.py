from src.core.types.player import PlayerState

def strategy_plan_generate_node(state: PlayerState) -> PlayerState:
    """
    初期戦略計画（Overall Strategic Plan）を生成するノード。
    夜フェーズ（night_started）の直後に実行されることを想定。

    責務:
    - PlayerMemory.strategy_plan が未設定の場合、StrategyPlanGenerator を用いて生成し保存する。
    """
    # Lazy import
    from src.game.player.strategy_plan_generator import strategy_plan_generator

    memory = state["memory"]

    if memory.strategy_plan is None:
        print("[strategy_plan_generate_node] generating initial strategy plan...")
        plan = strategy_plan_generator.generate(memory)
        if plan:
            memory.strategy_plan = plan
        else:
            print("[strategy_plan_generate_node] Failed to generate initial strategy plan")
    else:
        print("[strategy_plan_generate_node] Strategy plan already exists. Skipping.")

    return state
