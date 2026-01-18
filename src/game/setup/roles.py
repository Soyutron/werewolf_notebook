# game/setup/roles.py
"""
役職割り当てモジュール

責務:
- GameDefinition.role_distribution に基づいて役職をランダムに割り当てる
- プレイヤー人数と役職数の整合性検証

設計方針:
- GameDefinition を Single Source of Truth として使用
- 役職構成・人数の変更に柔軟に対応可能
"""
from __future__ import annotations

import random
from typing import TYPE_CHECKING, Dict, List

if TYPE_CHECKING:
    from src.core.types.phases import GameDefinition

# NOTE: PlayerName, RoleName は TypeAlias = str のため、
# 循環インポートを避けて str を直接使用する。


def assign_roles(
    players: List[str],
    definition: GameDefinition,
) -> Dict[str, str]:
    """
    プレイヤーに役職をランダムに割り当てる。

    Args:
        players: プレイヤー名のリスト
        definition: ゲーム定義（役職構成を含む）

    Returns:
        プレイヤー名 → 役職名 の辞書

    Raises:
        ValueError: プレイヤー人数と role_distribution の長さが一致しない場合

    設計方針:
    - GameDefinition.role_distribution を使用して任意の人数・役職構成に対応
    - シャッフルによりランダム配布を実現
    - テスト用に random.seed() で再現性を確保可能
    """
    if len(players) != len(definition.role_distribution):
        raise ValueError(
            f"Player count ({len(players)}) must match "
            f"role_distribution length ({len(definition.role_distribution)})"
        )

    roles = list(definition.role_distribution)
    random.shuffle(roles)

    return {player: role for player, role in zip(players, roles)}
