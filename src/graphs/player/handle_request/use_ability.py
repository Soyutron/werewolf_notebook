from src.core.types import PlayerState, PlayerOutput


def handle_use_ability(state: PlayerState) -> PlayerState:
    req = state["input"].request

    # request がなければ何もしない
    if req is None:
        state["output"] = None
        return state

    # use_ability 以外は来ない前提（最小構成）
    state["output"] = PlayerOutput(
        action="use_ability",
        payload={},  # とりあえず空
    )
    return state
