from src.game.setup.gm_setup import setup_game
from src.core.types import (
    GameDefinition,
    WorldState,
    PlayerState,
    PlayerName,
    RoleName,
    PlayerInput,
    PlayerOutput,
    GMState,
    GameDecision,
)
from typing import Dict
from src.core.controller import PlayerController
from src.graphs.gm_graph import gm_graph


# =========================
# ゲーム実行セッション
# =========================
# 1 回のゲームを実行するための実行コンテナ。
# GMState / PlayerState / 真実情報（役職）を保持し、
# GMGraph と PlayerGraph を仲介する責務を持つ。
#
# ・state の「所有者」
# ・Graph 自体は state を持たない
# ・将来的に Redis / DB に置き換え可能
class GameSession:
    def __init__(
        self,
        *,
        definition: GameDefinition,
        world_state: WorldState,
        player_states: Dict[PlayerName, PlayerState],
        controllers: dict[PlayerName, PlayerController],
        assigned_roles: Dict[PlayerName, RoleName],
        gm_graph,
    ):
        self.definition = definition
        # このゲームのルール定義（役職構成・フェーズ構成など）
        # ゲーム開始前に定義され、ゲーム中は不変（immutable）
        # setup_game や GMGraph の判断基準として参照される
        self.world_state = world_state
        # GM（進行役）が管理する現在の進行状態
        # イベントによって更新される「公開可能な状態」のみを含む
        self.player_states = player_states
        # 各プレイヤーが内部に持つ状態（記憶・推測・意図など）
        # PlayerGraph の入力・出力として更新される
        # GM は中身を解釈せず、実行と受け渡しのみを行う
        self.controllers = controllers
        # 各プレイヤーが持つ Controller
        # PlayerGraph の入力・出力として更新される
        self.assigned_roles = assigned_roles
        # 各プレイヤーに割り当てられた実際の役職
        # GM（裁定者）だけが知る「真実情報」
        # 夜行動の解決や勝敗判定にのみ使用され、
        # 議論フェーズや公開 state には決して含めない
        self.gm_graph = gm_graph
        # GMGraph

    @classmethod
    def create(cls, definition: GameDefinition) -> "GameSession":
        """
        ゲーム開始時の GameSession を生成する。

        - プレイヤー生成
        - 役職割り当て
        - PlayerState 初期化
        - GMState 初期化

        ※ このメソッド以外から
          GameSession を直接 new しない想定
        """

        players, assigned_roles, player_states, controllers = setup_game(definition)

        world_state = WorldState(
            phase="night",
            players=players,
            public_events=[],
        )

        return cls(
            definition=definition,
            world_state=world_state,
            player_states=player_states,
            controllers=controllers,
            assigned_roles=assigned_roles,
            gm_graph=gm_graph,
        )

    def run_player_turn(
        self,
        *,
        player: PlayerName,
        input: PlayerInput,
    ) -> PlayerOutput:
        """
        GM からの PlayerRequest を受け取り、
        対象プレイヤーに実行させ、その結果を返す。
        """

        state = self.player_states[player]
        state.input = input

        controller = self.controllers[player]

        output = controller.act(state=state)

        # state の確定保存（Session の責務）
        state.output = output
        self.player_states[player] = state

        return output

    def run_gm_step(self):
        """
        GMGraph が正しく invoke できるかを確認するための最小ステップ
        （まだ dispatch はしない）
        """

        gm_state = GMState(
            world_state=self.world_state,
            decision=GameDecision(),
        )

        result = self.gm_graph.invoke(gm_state)

        # デバッグ確認用
        print("=== GMGraph result ===")
        print(result)

        return result
