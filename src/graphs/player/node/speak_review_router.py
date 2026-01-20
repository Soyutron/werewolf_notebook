# src/graphs/player/node/speak_review_router.py
from src.core.types.player import PlayerState

MAX_SPEAK_REVIEW_COUNT = 3


def speak_review_router_node(state: PlayerState) -> str:
    """
    生成された発言をレビューし、
    採用（commit）するか、再生成（refine）するかを判定する Router ノード。

    戻り値:
    - "commit": 発言を確定して出力する
    - "refine": 発言を作り直す
    """
    # Lazy import to avoid circular import
    from src.game.player.speak_reviewer import speak_reviewer

    print("[speak_review_router_node] Reviewing speech...")

    memory = state["memory"]
    internal = state["internal"]
    pending_speak = internal.pending_speak
    pending_strategy = internal.pending_strategy

    # 最大レビュー回数を超えた場合は強制的に commit
    if internal.speak_review_count >= MAX_SPEAK_REVIEW_COUNT:
        print(
            f"[speak_review_router_node] Max review count ({MAX_SPEAK_REVIEW_COUNT}) reached, forcing commit"
        )
        return "commit"

    # 発言が存在しない場合は安全側に倒す
    if pending_speak is None:
        print("[speak_review_router_node] No pending speech, forcing commit")
        return "commit"

    # 戦略が存在しない場合もレビューをスキップ
    if pending_strategy is None:
        print("[speak_review_router_node] No strategy found, forcing commit")
        return "commit"

    review_result = speak_reviewer.review(
        speak=pending_speak,
        strategy=pending_strategy,
        memory=memory,
        game_def=state.get("game_def"),
    )

    # レビューに失敗した場合は安全側に倒す
    if review_result is None:
        print("[speak_review_router_node] Review failed, forcing commit")
        return "commit"

    internal.last_speak_review = review_result
    internal.speak_review_count += 1

    if review_result.needs_fix:
        print(f"[speak_review_router_node] Speech needs fix: {review_result.reason}")
        return "refine"

    print("[speak_review_router_node] Speech approved")
    return "commit"

