from src.core.types import PlayerState


def phase_router(state: PlayerState) -> str:
    """
    PlayerGraph の START からの分岐を決定する。

    - divine_result : GM から占い結果などの「通知イベント」
    - use_ability   : プレイヤーが能力を使うターン
    """
    player_input = state.get("input")

    # event が来ている場合（GM → Player の一方通行通知）
    if player_input.event is not None:
        if player_input.event.event_type == "night_started":
            return "night_started"

        if player_input.event.event_type == "day_started":
            return "day_started"

        if player_input.event.event_type == "divine_result":
            return "divine_result"

        if player_input.event.event_type == "gm_comment":
            return "gm_comment"

        if player_input.event.event_type == "speak":
            return "interpret_speech"

        if player_input.event.event_type == "role_swapped":
            return "role_swapped"

    # request が来ている場合（Player の行動ターン）
    if player_input.request is not None:
        if player_input.request.request_type == "use_ability":
            return "use_ability"

        if player_input.request.request_type == "speak":
            return "belief_update"

        if player_input.request.request_type == "vote":
            return "vote"

    # -------------------------
    # どれにも当てはまらないのは設計ミス
    # -------------------------
    raise RuntimeError(
        player_input,
        "phase_router: neither event nor request is present in PlayerInput",
    )
