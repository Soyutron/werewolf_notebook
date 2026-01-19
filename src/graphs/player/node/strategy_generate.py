# src/graphs/player/node/strategy_generate.py
from src.core.types.player import PlayerState


def strategy_generate_node(state: PlayerState) -> PlayerState:
    """
    戦略を生成するノード。

    責務:
    - PlayerMemory から現在の状況を読み取る
    - 役職に応じた戦略を生成する
    - 生成した戦略を internal.pending_strategy に保存する
    """
    # Lazy import to avoid circular import
    from src.game.player.strategy_generator import strategy_generator
    from src.game.player.strategy_plan_generator import strategy_plan_generator

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
        else:
            print("[strategy_generate_node] Failed to generate initial strategy plan")
            # 失敗してもAction Guideline生成は試みる（Planなしで）

    # 2. 今回の発言のための行動指針（Action Guideline）を生成する
    strategy = strategy_generator.generate_action_guideline(
        memory=memory,
        plan=memory.strategy_plan
    )

    if strategy is None:
        print("[strategy_generate_node] Failed to generate strategy")
        return state

    internal.pending_strategy = strategy

    return state

