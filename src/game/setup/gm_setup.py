# game/setup/gm_setup.py
"""
ゲームセットアップモジュール

責務:
- プレイヤー生成
- 役職割り当て
- PlayerMemory 初期化
- Controller 初期化

設計方針:
- GameDefinition を Single Source of Truth として使用
- プレイヤー人数は role_distribution から自動決定
"""
from __future__ import annotations

from typing import TYPE_CHECKING, Dict, List, Tuple

from src.game.setup.players import create_players
from src.game.setup.roles import assign_roles
from src.game.setup.memory import create_initial_player_memory

if TYPE_CHECKING:
    from src.core.types.player import PlayerName, PlayerMemory
    from src.core.types.roles import RoleName
    from src.core.types.phases import GameDefinition
    from src.core.controller import PlayerController


def setup_game(
    definition: GameDefinition,
) -> Tuple[
    List[PlayerName],
    Dict[PlayerName, RoleName],
    Dict[PlayerName, PlayerMemory],
    Dict[PlayerName, PlayerController],
]:
    """
    ゲーム初期状態を構築する。

    この関数の責務:
    - プレイヤー一覧の生成
    - 役職の割り当て（GM 視点の真実）
    - 各 PlayerMemory の初期化

    設計方針:
    - GameDefinition.role_distribution を Single Source of Truth として使用
    - プレイヤー人数は role_distribution から自動決定
    - role_distribution の内容に応じて任意の役職構成に対応
    """
    # Lazy import to avoid circular import
    from src.graphs.player.player_graph import player_graph
    from src.core.controller import AIPlayerController

    # 1. プレイヤー人数は role_distribution から決定
    player_count = len(definition.role_distribution)
    players = create_players(player_count)

    # 2. 役職配布（GameDefinition を使用）
    assigned_roles = assign_roles(players, definition)

    # 3. PlayerMemory 初期化
    player_memories = {
        player: create_initial_player_memory(
            definition=definition,
            self_name=player,
            self_role=assigned_roles[player],
            players=players,
        )
        for player in players
    }

    # 4. Controller 初期化（AI N人）
    controllers = {player: AIPlayerController(player_graph) for player in players}

    return players, assigned_roles, player_memories, controllers
