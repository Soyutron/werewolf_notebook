# game/setup/gm_setup.py
from typing import Dict, List, Tuple

from src.core.types import PlayerName, RoleName, PlayerMemory
from src.game.setup.players import create_players
from src.game.setup.roles import assign_roles
from src.game.setup.memory import create_initial_player_memory
from src.core.types import GameDefinition
from src.core.controller import PlayerController
from src.core.controller import AIPlayerController
from src.graphs.player.player_graph import player_graph


def setup_game(
    definition: GameDefinition,
    # NOTE: 現在はワンナイト人狼固定構成のため definition は未使用。
    # 将来、player_count / role_distribution を definition から取得する。
) -> Tuple[
    List[PlayerName],
    Dict[PlayerName, RoleName],
    Dict[PlayerName, PlayerMemory],
    Dict[PlayerName, PlayerController],
]:
    """
    ワンナイト人狼のゲーム初期状態を構築する。

    この関数の責務:
    - プレイヤー一覧の生成
    - 役職の割り当て（GM 視点の真実）
    - 各 PlayerMemory の初期化

    設計方針:
    - ゲーム開始時に一度だけ呼ばれる
    - ここで生成された PlayerMemory は PlayerGraph に渡され、
      以後 GM は中身を直接変更しない
    """

    # 1. プレイヤー生成（5人固定）
    players: List[PlayerName] = create_players()

    # 2. 役職配布（GM のみが知る）
    assigned_roles: Dict[PlayerName, RoleName] = assign_roles(players)

    # 3. PlayerMemory 初期化
    player_memories: Dict[PlayerName, PlayerMemory] = {
        player: create_initial_player_memory(
            definition=definition,
            self_name=player,
            self_role=assigned_roles[player],
            players=players,
        )
        for player in players
    }

    # 4. Controller 初期化（AI 5人）
    controllers = {player: AIPlayerController(player_graph) for player in players}

    return players, assigned_roles, player_memories, controllers
