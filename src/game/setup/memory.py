# game/setup/memory.py
from typing import Dict, List
from src.core.types import PlayerName, RoleName, PlayerMemory, GameDefinition, RoleProb


def create_initial_player_memory(
    *,
    definition: GameDefinition,
    self_name: PlayerName,
    self_role: RoleName,
    players: List[PlayerName],
) -> PlayerMemory:
    """
    PlayerMemory の初期状態を生成する。

    設計方針:
    - GM がゲーム開始時に一度だけ呼ぶ
    - PlayerGraph はこの memory を以後ずっと保持・更新する
    - GM は初期化後、この中身を直接変更しない

    初期状態の考え方:
    - 自分の役職は確定（確率 1.0）
    - 他プレイヤーは役職の事前分布（均等）
    - observed_events / history は空
    """

    all_roles = definition.roles

    uniform_prob = 1.0 / len(all_roles)

    role_beliefs: Dict[PlayerName, RoleProb] = {}

    for player in players:
        if player == self_name:
            # 自分自身の役職は確定（他は 0.0 で明示）
            role_beliefs[player] = RoleProb(
                probs={role: (1.0 if role == self_role else 0.0) for role in all_roles}
            )
        else:
            # 他プレイヤーは事前分布（均等）
            role_beliefs[player] = RoleProb(
                probs={role: uniform_prob for role in all_roles}
            )

    return PlayerMemory(
        self_name=self_name,
        self_role=self_role,
        players=players,
        observed_events=list(),
        role_beliefs=role_beliefs,
        history=list(),
    )
