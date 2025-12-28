# game/setup/memory.py
from typing import Dict, Literal, List
from src.core.types import PlayerName, RoleName, PlayerMemory


def create_initial_player_memory(
    *,
    self_name: PlayerName,
    self_role: RoleName,
    all_players: List[PlayerName],
) -> PlayerMemory:
    """
    PlayerMemory の初期状態を生成する。

    設計方針:
    - GM がゲーム開始時に一度だけ呼ぶ
    - PlayerGraph はこの memory を以後ずっと保持・更新する
    - GM は初期化後、この中身を直接変更しない

    初期状態の考え方:
    - 自分以外の役職はすべて unknown
    - 疑い度は全員 0.5（中立）からスタート
    - history は空
    """

    beliefs: Dict[PlayerName, RoleName | Literal["unknown"]] = {
        p: "unknown" for p in all_players if p != self_name
    }

    suspicion: Dict[PlayerName, float] = {p: 0.5 for p in all_players if p != self_name}

    return PlayerMemory(
        self_name=self_name,
        self_role=self_role,
        beliefs=beliefs,
        suspicion=suspicion,
        history=list(),
    )
