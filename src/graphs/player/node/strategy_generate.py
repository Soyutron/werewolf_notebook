# src/graphs/player/node/strategy_generate.py
from src.core.types.player import PlayerState


def strategy_generate_node(state: PlayerState) -> PlayerState:
    """
    戦略を生成するノード。

    責務:
    - PlayerMemory から現在の状況を読み取る
    - 役職に応じた戦略を生成する
    - マイルストーン状態を更新する（milestone_status）
    - 発言方針重みを算出する（policy_weights）
    - 生成した戦略を internal.pending_strategy に保存する
    """
    # Lazy import to avoid circular import
    from src.game.player.strategy_generator import strategy_generator
    from src.game.player.strategy_plan_generator import strategy_plan_generator
    from src.game.player.milestone_status_updater import milestone_status_updater
    from src.game.player.policy_weights_calculator import policy_weights_calculator
    from src.core.memory.strategy import PlayerMilestoneStatus

    print("[strategy_generate_node] Generating strategy...")

    memory = state["memory"]
    internal = state["internal"]

    # 1. 初期戦略計画（Night Phase）が未生成なら生成する
    #    本来は夜フェーズでやるべきだが、現状のグラフ構造上、初回の発言機会に生成する
    if memory.strategy_plan is None:
        print("[strategy_generate_node] generating initial strategy plan...")
        plan = strategy_plan_generator.generate(memory)
        if plan:
            memory.strategy_plan = plan
            # マイルストーン状態を初期化
            if plan.milestone_plan and plan.milestone_plan.milestones:
                memory.milestone_status = milestone_status_updater.initialize_status(
                    plan.milestone_plan
                )
        else:
            print("[strategy_generate_node] Failed to generate initial strategy plan")
            # 失敗してもAction Guideline生成は試みる（Planなしで）

    # 2. マイルストーン状態を更新（新しいイベントに基づく）
    if memory.strategy_plan and memory.strategy_plan.milestone_plan:
        if memory.milestone_status is None:
            memory.milestone_status = milestone_status_updater.initialize_status(
                memory.strategy_plan.milestone_plan
            )
        
        # 直近のイベントを取得（まだ反映されていないもの）
        # NOTE: 現在は全イベントを渡しているが、将来的には
        #       last_milestone_update_index などで差分管理する
        memory.milestone_status = milestone_status_updater.update(
            milestone_plan=memory.strategy_plan.milestone_plan,
            current_status=memory.milestone_status,
            new_events=memory.observed_events,
        )

    # 3. 発言方針重みを算出
    if memory.strategy_plan and memory.milestone_status:
        memory.policy_weights = policy_weights_calculator.calculate(
            milestone_plan=memory.strategy_plan.milestone_plan,
            milestone_status=memory.milestone_status,
            strategy_plan=memory.strategy_plan,
        )

    # 4. 今回の発言のための行動指針（Action Guideline）を生成する
    strategy = strategy_generator.generate_action_guideline(
        memory=memory,
        plan=memory.strategy_plan
    )

    if strategy is None:
        print("[strategy_generate_node] Failed to generate strategy")
        return state

    internal.pending_strategy = strategy

    return state


