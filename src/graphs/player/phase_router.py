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
        if player_input.event.event_type == "divine_result":
            return "divine_result"

    # request が来ている場合（Player の行動ターン）
    if player_input.request is not None:
        return "use_ability"

    # どちらでもない場合はデフォルト
    return "use_ability"
