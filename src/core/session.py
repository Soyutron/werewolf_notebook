from src.game.setup.gm_setup import setup_game
from src.core.types import (
    GameDefinition,
    WorldState,
    PlayerState,
    PlayerName,
    RoleName,
    PlayerInput,
    PlayerOutput,
    GMGraphState,
    GameDecision,
)
from typing import Dict
from src.core.controller import PlayerController
from src.graphs.gm_graph import gm_graph


# =========================
# ゲーム実行セッション
# =========================
# 1 回のゲームを実行するための実行コンテナ。
# worldState / PlayerState / 真実情報（役職）を保持し、
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
        - world_state 初期化

        ※ このメソッド以外から
          GameSession を直接 new しない想定
        """

        players, assigned_roles, player_memories, controllers = setup_game(definition)

        # PlayerMemory を PlayerState にラップする
        player_states = {
            player: PlayerState(
                memory=memory,
                input=PlayerInput(),
                output=None,
            )
            for player, memory in player_memories.items()
        }

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
    ) -> PlayerOutput | None:
        """
        GM からの PlayerRequest を受け取り、
        対象プレイヤーに実行させ、その結果を返す。

        - input は一時的な刺激
        - output は毎ターン初期化される
        """

        state = self.player_states[player]

        # --- 毎ターンの初期化（重要） ---
        state.input = input
        state.output = None

        controller = self.controllers[player]

        # --- 行動要求がある場合のみ act ---
        if input.request is None:
            # 行動要求がない = 待機ターン
            self.player_states[player] = state
            return None

        output = controller.act(state=state)

        # --- 結果の確定保存（Session の責務） ---
        state.output = output
        self.player_states[player] = state

        return output

    def run_gm_step(self) -> GMGraphState:
        """
        GMGraph が正しく invoke できるかを確認するための最小ステップ
        （まだ dispatch はしない）
        """

        gm_graph_state = GMGraphState(
            world_state=self.world_state,
            decision=GameDecision(),
        )

        gm_graph_state = self.gm_graph.invoke(gm_graph_state)

        # デバッグ確認用
        print("=== GMGraph result ===")
        print(gm_graph_state)

        self.world_state = gm_graph_state.world_state

        return gm_graph_state

    def dispatch(self, decision: GameDecision) -> None:
        """
        GMGraph からの GameDecision を受け取り、
        各プレイヤーに実行させる。
        """

        # プレイヤーへの行動要求を dispatch
        if decision.requests:
            for player, request in decision.requests.items():
                self.run_player_turn(
                    player=player,
                    input=PlayerInput(
                        request=request,
                    ),
                )

        # 公開イベントを反映
        if decision.events:
            self.world_state.public_events.extend(decision.events)

        # フェーズ遷移
        if decision.next_phase is not None:
            self.world_state.phase = decision.next_phase
