# src/graphs/player/node/strategy_refine.py
from src.core.types.player import PlayerState


def strategy_refine_node(state: PlayerState) -> PlayerState:
    """
    戦略をレビュー指摘を踏まえて再生成するノード。

    責務:
    - 直前の StrategyReview（internal.last_strategy_review）を反映する
    - 再生成した戦略を internal.pending_strategy に上書きする
    """
    # Lazy import to avoid circular import
    from src.game.player.strategy_refiner import strategy_refiner

    print("[strategy_refine_node] Refining strategy...")

    memory = state["memory"]
    internal = state["internal"]

    # レビューが存在しない場合は何もしない（安全装置）
    if internal.last_strategy_review is None:
        print("[strategy_refine_node] No review found, skipping")
        return state

    # 戦略が存在しない場合は何もしない
    if internal.pending_strategy is None:
        print("[strategy_refine_node] No pending strategy, skipping")
        return state

    refined_strategy = strategy_refiner.refine(
        original=internal.pending_strategy,
        review=internal.last_strategy_review,
        memory=memory,
    )

    if refined_strategy is None:
        print("[strategy_refine_node] Failed to refine strategy")
        return state

    # pending を上書き
    internal.pending_strategy = refined_strategy

    return state

