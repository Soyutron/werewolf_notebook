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

    print("[strategy_generate_node] Generating strategy...")

    memory = state["memory"]
    internal = state["internal"]

    strategy = strategy_generator.generate(memory=memory)

    if strategy is None:
        print("[strategy_generate_node] Failed to generate strategy")
        return state

    internal.pending_strategy = strategy

    return state

