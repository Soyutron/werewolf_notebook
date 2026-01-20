# src/graphs/player/node/speak_generate.py
from src.core.types.player import PlayerState


def speak_generate_node(state: PlayerState) -> PlayerState:
    """
    戦略に基づいて発言を生成するノード。

    責務:
    - 確定した戦略（internal.pending_strategy）を読み取る
    - 戦略に基づいた発言を生成する
    - 生成した発言を internal.pending_speak に保存する
    """
    # Lazy import to avoid circular import
    from src.game.player.speak_generator import speak_generator

    print("[speak_generate_node] Generating speech...")

    memory = state["memory"]
    internal = state["internal"]
    request = state["input"].request

    if request is None:
        print("[speak_generate_node] No request found, skipping")
        return state

    # 戦略が存在するか確認（本来は strategy_generate_node で生成されているべき）
    if internal.pending_strategy is None:
        print(f"[speak_generate_node] WARNING: No strategy available for speech generation. Strategy consistency may be compromised.")

    # 戦略を発言生成に渡す
    # Strategy が渡されることで、strategy_plan_generator.py → strategy_generator.py の
    # 戦略フローが speak_generator.py まで一貫して適用される
    # policy_weights はマイルストーン状態から算出された発言方針調整パラメータ
    speak = speak_generator.generate(
        memory=memory,
        observed=request,
        game_def=state.get("game_def"),
        strategy=internal.pending_strategy,
        policy_weights=memory.policy_weights,
    )

    if speak is None:
        print("[speak_generate_node] Failed to generate speech")
        return state

    internal.pending_speak = speak

    return state


