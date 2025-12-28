from src.core.types import PlayerState, PlayerOutput, NoAbility, WerewolfAbility, SeerAbility


def handle_use_ability(state: PlayerState) -> PlayerState:
    req = state["input"].request

    # request がなければ何もしない
    if req is None:
        state["output"] = None
        return state

    role = state["memory"].self_role

    if role == "seer":
        return handle_seer_ability(state)
    elif role == "werewolf":
        return handle_werewolf_ability(state)
    elif role == "villager":
        return handle_villager_ability(state)
    elif role == "madman":
        return handle_madman_ability(state)
    else:
        raise ValueError(f"Unknown role: {role}")


def handle_seer_ability(state: PlayerState) -> PlayerState:
    self_name = state["memory"].self_name
    all_players = state["memory"].all_players

    # 自分以外を候補にする
    candidates = [p for p in all_players if p != self_name]

    target = random.choice(candidates) if candidates else None
    
    state["output"] = PlayerOutput(
        action="use_ability",
        payload=SeerAbility(kind="seer", target=target),
    )
    return state


def handle_werewolf_ability(state: PlayerState) -> PlayerState:
    state["output"] = PlayerOutput(
        action="use_ability",
        payload=WerewolfAbility(kind="werewolf"),
    )
    return state


def handle_villager_ability(state: PlayerState) -> PlayerState:
    state["output"] = PlayerOutput(
        action="use_ability",
        payload=NoAbility(kind="none"),
    )
    return state


def handle_madman_ability(state: PlayerState) -> PlayerState:
    state["output"] = PlayerOutput(
        action="use_ability",
        payload=NoAbility(kind="none"),
    )
    return state
