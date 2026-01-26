from src.core.types import (
    PlayerState,
    PlayerOutput,
    NoAbility,
    WerewolfAbility,
    SeerAbility,
    ThiefAbility,
)
import random


def handle_use_ability(state: PlayerState) -> PlayerState:
    req = state["input"].request

    # request がなければ何もしない
    if req is None:
        state["output"] = None
        return state

    role_name = state["memory"].self_role
    game_def = state.get("game_def")
    
    # GameDefinition が state に注入されていることを前提とする
    if not game_def:
        raise RuntimeError("GameDefinition is not injected in PlayerState")

    role_def = game_def.roles.get(role_name)
    if not role_def:
        raise ValueError(f"Role '{role_name}' is not defined in GameDefinition.roles")

    ability_type = role_def.ability_type

    if ability_type == "seer":
        return handle_seer_ability(state)
    elif ability_type == "werewolf":
        return handle_werewolf_ability(state)
    elif ability_type == "thief":
        return handle_thief_ability(state)
    else:
        # ability_type == "none" または未知の能力タイプは能力なしとして扱う
        return handle_no_ability(state)


def handle_seer_ability(state: PlayerState) -> PlayerState:
    self_name = state["memory"].self_name
    players = state["memory"].players

    # 自分以外を候補にする
    candidates = [p for p in players if p != self_name]

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


def handle_no_ability(state: PlayerState) -> PlayerState:
    state["output"] = PlayerOutput(
        action="use_ability",
        payload=NoAbility(kind="none"),
    )
    return state


def handle_thief_ability(state: PlayerState) -> PlayerState:
    """
    怪盗の能力ハンドラ。

    自分以外のプレイヤー1名をランダムに選択し、
    役職交換の対象とする。
    
    実際の役職交換処理は ActionResolver で実行される。
    """
    self_name = state["memory"].self_name
    players = state["memory"].players

    # 自分以外を候補にする
    candidates = [p for p in players if p != self_name]
    target = random.choice(candidates) if candidates else None

    state["output"] = PlayerOutput(
        action="use_ability",
        payload=ThiefAbility(kind="thief", target=target),
    )
    print(f"[DEBUG] handle_thief_ability: {state['memory'].self_name} selected target={target}")
    return state
