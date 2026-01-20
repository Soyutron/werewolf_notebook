# src/graphs/player/node/speak_refine.py
from src.core.types.player import PlayerState


def speak_refine_node(state: PlayerState) -> PlayerState:
    """
    発言をレビュー指摘を踏まえて再生成するノード。

    責務:
    - 直前の SpeakReview（internal.last_speak_review）を反映する
    - 戦略（internal.pending_strategy）との整合性を保つ
    - 再生成した発言を internal.pending_speak に上書きする
    """
    # Lazy import to avoid circular import
    from src.game.player.speak_refiner import speak_refiner

    print("[speak_refine_node] Refining speech...")

    memory = state["memory"]
    internal = state["internal"]

    # レビューが存在しない場合は何もしない（安全装置）
    if internal.last_speak_review is None:
        print("[speak_refine_node] No review found, skipping")
        return state

    # 発言が存在しない場合は何もしない
    if internal.pending_speak is None:
        print("[speak_refine_node] No pending speech, skipping")
        return state

    # 戦略が存在しない場合は何もしない
    if internal.pending_strategy is None:
        print("[speak_refine_node] No strategy found, skipping")
        return state

    refined_speak = speak_refiner.refine(
        original=internal.pending_speak,
        strategy=internal.pending_strategy,
        review=internal.last_speak_review,
        memory=memory,
        game_def=state.get("game_def"),
    )

    if refined_speak is None:
        print("[speak_refine_node] Failed to refine speech")
        return state

    # pending を上書き
    internal.pending_speak = refined_speak

    return state

