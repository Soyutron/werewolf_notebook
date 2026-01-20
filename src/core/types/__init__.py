"""
types パッケージ - 全ての型定義を再エクスポート

後方互換性のため、既存の `from src.core.types import ...` を
そのまま動作させるための集約モジュール。

ドメイン別モジュール:
- roles.py   : 役職・陣営
- phases.py  : フェーズ・ゲーム定義・ワールド状態
- player.py  : プレイヤー関連
- events.py  : イベント・リクエスト
- gm.py      : GM 進行管理
"""

# 役職・陣営
from src.core.types.roles import (
    RoleName,
    Side,
    DaySide,
    WinSide,
    RoleDefinition,
)

# イベント・リクエスト
from src.core.types.events import (
    GameEventType,
    GameEvent,
    PlayerRequestType,
    PlayerRequest,
)

# プレイヤー関連
from src.core.types.player import (
    PlayerName,
    RoleProb,
    PlayerMemory,
    PlayerInput,
    PlayerOutput,
    PlayerState,
    PlayerInternalState,
    NoAbility,
    SeerAbility,
    WerewolfAbility,
    ThiefAbility,
    AbilityResult,
    Vote,
)

# フェーズ・ゲーム定義・ワールド状態
from src.core.types.phases import (
    Phase,
    GameDefinition,
    WorldState,
    GameResult,
)

# GM 進行管理
from src.core.types.gm import (
    GameDecision,
    GMInternalState,
    GMGraphState,
)

__all__ = [
    # roles
    "RoleName",
    "RoleProb",
    "Side",
    "DaySide",
    "WinSide",
    "RoleDefinition",
    # events
    "GameEventType",
    "GameEvent",
    "PlayerRequestType",
    "PlayerRequest",
    # player
    "PlayerName",
    "PlayerMemory",
    "PlayerInput",
    "PlayerOutput",
    "PlayerState",
    "PlayerInternalState",
    "NoAbility",
    "SeerAbility",
    "WerewolfAbility",
    "ThiefAbility",
    "AbilityResult",
    "Vote",
    # phases
    "Phase",
    "GameDefinition",
    "WorldState",
    "GameResult",
    # gm
    "GameDecision",
    "GMInternalState",
    "GMGraphState",
]
