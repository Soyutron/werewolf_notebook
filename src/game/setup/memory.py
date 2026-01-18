# game/setup/memory.py
"""
プレイヤーメモリ初期化モジュール

責務:
- GameDefinition に基づいて PlayerMemory の初期状態を生成する
- 役職確率の事前分布を計算する

設計方針:
- 自分の役職は確率 1.0 で確定
- 他プレイヤーは role_distribution に基づく事前分布
"""
from __future__ import annotations

from typing import TYPE_CHECKING, Dict, List
from collections import Counter

if TYPE_CHECKING:
    from src.core.types.player import PlayerName, PlayerMemory, RoleProb
    from src.core.types.roles import RoleName
    from src.core.types.phases import GameDefinition


def make_prior_role_prob(definition: GameDefinition) -> dict[str, float]:
    """
    role_distribution から役職の事前確率分布を作る。
    同じ役職が複数ある場合は合算される。
    """
    all_roles = definition.roles.keys()
    counter = Counter(definition.role_distribution)
    total = len(definition.role_distribution)

    return {role: counter.get(role, 0) / total for role in all_roles}


def create_initial_player_memory(
    *,
    definition: GameDefinition,
    self_name: str,
    self_role: str,
    players: List[str],
) -> PlayerMemory:
    """
    PlayerMemory の初期状態を生成する。

    初期状態:
    - 自分の役職は確定（確率 1.0）
    - 他プレイヤーは role_distribution に基づく事前分布
    - observed_events / history は空
    """
    # Lazy import to avoid circular import at module level
    from src.core.types.player import PlayerMemory, RoleProb

    role_beliefs: Dict[str, RoleProb] = {}

    all_roles = definition.roles.keys()
    prior_probs = make_prior_role_prob(definition)

    for player in players:
        if player == self_name:
            # 自分自身の役職は確定
            role_beliefs[player] = RoleProb(
                probs={role: (1.0 if role == self_role else 0.0) for role in all_roles}
            )
        else:
            # 他プレイヤーは role_distribution 由来の事前分布
            role_beliefs[player] = RoleProb(
                probs={role: prior_probs[role] for role in all_roles}
            )

    return PlayerMemory(
        self_name=self_name,
        self_role=self_role,
        players=players,
        observed_events=[],
        role_beliefs=role_beliefs,
        history=[],
    )
