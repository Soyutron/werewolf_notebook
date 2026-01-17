# src/graphs/player/node/strategy_review_router.py
from src.core.types.player import PlayerState

MAX_STRATEGY_REVIEW_COUNT = 3


def strategy_review_router_node(state: PlayerState) -> str:
    """
    生成された戦略をレビューし、
    採用（commit）するか、再生成（refine）するかを判定する Router ノード。

    戻り値:
    - "commit": 戦略を確定して発言生成に進む
    - "refine": 戦略を作り直す
    """
    # Lazy import to avoid circular import
    from src.game.player.strategy_reviewer import strategy_reviewer

    print("[strategy_review_router_node] Reviewing strategy...")

    memory = state["memory"]
    internal = state["internal"]
    pending_strategy = internal.pending_strategy

    # 最大レビュー回数を超えた場合は強制的に commit
    if internal.strategy_review_count >= MAX_STRATEGY_REVIEW_COUNT:
        print(
            f"[strategy_review_router_node] Max review count ({MAX_STRATEGY_REVIEW_COUNT}) reached, forcing commit"
        )
        return "commit"

    # 戦略が存在しない場合は安全側に倒す
    if pending_strategy is None:
        print("[strategy_review_router_node] No pending strategy, forcing commit")
        return "commit"

    review_result = strategy_reviewer.review(
        strategy=pending_strategy,
        memory=memory,
    )

    # レビューに失敗した場合は安全側に倒す
    if review_result is None:
        print("[strategy_review_router_node] Review failed, forcing commit")
        return "commit"

    internal.last_strategy_review = review_result
    internal.strategy_review_count += 1

    if review_result.needs_fix:
        print(
            f"[strategy_review_router_node] Strategy needs fix: {review_result.reason}"
        )
        return "refine"

    print("[strategy_review_router_node] Strategy approved")
    return "commit"

