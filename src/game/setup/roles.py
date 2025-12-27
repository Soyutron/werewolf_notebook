# game/setup/roles.py
import random
from typing import Dict, List
from src.core.types import PlayerName, RoleName


# =========================
# 固定役職構成（5人村）
# =========================
# ワンナイト人狼想定：
# - 村人 x2
# - 人狼 x1
# - 占い師 x1
# - 狂人 x1
DEFAULT_ROLES: List[RoleName] = [
    "villager",
    "villager",
    "werewolf",
    "seer",
    "madman",
]


def assign_roles(players: List[PlayerName]) -> Dict[PlayerName, RoleName]:
    """
    プレイヤーに役職をランダムに割り当てる。

    現段階の仕様:
    - プレイヤー人数は5人固定
    - 役職構成は固定（村村狼占狂）
    - シャッフルしてランダム配布する

    将来拡張:
    - 人数可変
    - role_distribution を GameDefinition から受け取る
    - テスト用に shuffle 無効化
    """

    if len(players) != 5:
        raise ValueError("Current one-night werewolf setup supports exactly 5 players.")

    roles = DEFAULT_ROLES.copy()
    random.shuffle(roles)

    return {player: role for player, role in zip(players, roles)}
