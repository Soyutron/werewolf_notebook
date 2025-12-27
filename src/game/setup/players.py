# game/setup/players.py
from typing import List
from src.core.types import PlayerName


DEFAULT_PLAYERS: List[PlayerName] = [
    "太郎",
    "花子",
    "次郎",
    "さくら",
    "健太",
]


def create_players(player_count: int = 5) -> List[PlayerName]:
    """
    ワンナイト人狼用のプレイヤー一覧を生成する。

    現段階では:
    - 人数は5人固定を想定
    - 日本語名を使用して可読性を高める

    将来拡張:
    - player_count 可変
    - 設定ファイル / UI / LLM 由来の名前
    """

    if player_count != 5:
        raise ValueError("Current one-night werewolf setup supports exactly 5 players.")

    return DEFAULT_PLAYERS.copy()
