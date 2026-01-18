# game/setup/players.py
"""
プレイヤー生成モジュール

責務:
- 指定された人数のプレイヤー名リストを生成する
- 可読性のある日本語名を提供する

設計方針:
- プレイヤー名プールを用意し、人数に応じて選択
- プール不足時はフォールバック命名を使用
- 将来的には設定ファイル/UI/LLM由来の名前にも対応可能
"""
from typing import List

# NOTE: PlayerName は TypeAlias = str のため、循環インポートを避けて
# str を直接使用する。型ヒントとしては同等。


# 最大人数のプレイヤー名プール
# 可読性を重視した日本語名を使用
DEFAULT_PLAYER_POOL: List[str] = [
    "太郎",
    "花子",
    "次郎",
    "さくら",
    "健太",
    "美咲",
    "隼人",
    "あかり",
    "蓮",
    "結衣",
]


def create_players(player_count: int) -> List[str]:
    """
    指定された人数分のプレイヤー名リストを生成する。

    Args:
        player_count: 生成するプレイヤー数

    Returns:
        プレイヤー名のリスト

    Raises:
        ValueError: player_count が 0 以下の場合

    動作:
    - プールに十分な名前がある場合: プールから選択
    - プールが不足する場合: 「Player_N」形式でフォールバック生成
    """
    if player_count <= 0:
        raise ValueError("player_count must be positive")

    if player_count <= len(DEFAULT_PLAYER_POOL):
        return DEFAULT_PLAYER_POOL[:player_count]

    # プール不足時のフォールバック
    players = DEFAULT_PLAYER_POOL.copy()
    for i in range(len(DEFAULT_PLAYER_POOL), player_count):
        players.append(f"Player_{i + 1}")
    return players
