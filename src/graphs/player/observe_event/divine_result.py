from src.core.types import PlayerState, RoleName, PlayerName, RoleProb


def handle_divine_result(state: PlayerState) -> PlayerState:
    """
    占い結果を受け取り、占い師の記憶（role_beliefs）を更新するノード。

    設計方針:
    - divine_result は占い師本人にのみ届く「確定情報」
    - beliefs / suspicion のような単純ラベルは使わない
    - role_beliefs（確率分布）を直接更新する
    - 行動は発生しない（output は None）
    """

    event = state["input"].event
    if event is None or event.event_type != "divine_result":
        return state

    target: PlayerName = event.payload["target"]
    revealed_role: RoleName = event.payload["role"]

    memory = state["memory"]

    # -------------------------
    # 1. 役職確率分布の確定更新
    # -------------------------
    # 占いは「確定情報」なので、
    # 対象プレイヤーの役職確率を 100% / 0% にする
    probs: dict[RoleName, float] = {}

    for role in memory.role_beliefs[target].probs.keys():
        probs[role] = 1.0 if role == revealed_role else 0.0

    memory.role_beliefs[target] = RoleProb(probs=probs)

    # -------------------------
    # 2. 観測イベントの保存
    # -------------------------
    # divine_result は private event だが、
    # 「自分が観測した事実」としては保存してよい
    memory.observed_events.append(event)

    # 行動はしない
    state["output"] = None
    return state
