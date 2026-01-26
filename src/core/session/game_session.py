"""
GameSession - ゲーム実行セッション（state の唯一所有者）

1 回のゲームを実行するための実行コンテナ。

このクラスは「ゲームという1つの世界」を管理する中心的な存在であり、
以下の役割を持つ：

- WorldState / PlayerState / 真実情報（役職）を保持する
- GMGraph と PlayerGraph の実行を仲介・調停する
- Graph が返した結果を「正式な状態」として確定させる

重要な設計方針：
・state の「唯一の所有者」は GameSession
・Graph（GMGraph / PlayerGraph）は state を保持しない
・Graph は常に「与えられた state を加工して返す」だけ
・将来的に Redis / DB に state を永続化する場合も、
  差し替え先はこの GameSession のみ

責務の委譲:
・ActionResolver: PlayerOutput の解釈 → 副作用決定
・Dispatcher: GameDecision の適用
・PhaseRunner: フェーズ進行制御
"""

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
    GMInternalState,
)
from typing import Dict
from src.core.controller import PlayerController
from src.graphs.gm.gm_graph import GMGraph, gm_graph
from copy import deepcopy

from src.core.session.action_resolver import ActionResolver
from src.core.session.dispatcher import Dispatcher
from src.core.session.phase_runner import PhaseRunner


class GameSession:
    """
    ゲーム実行セッション - state の唯一所有者

    このクラスは「ゲームという1つの世界」を管理する中心的な存在であり、
    以下の役割を持つ：

    - WorldState / PlayerState / 真実情報（役職）を保持する
    - GMGraph と PlayerGraph の実行を仲介・調停する
    - Graph が返した結果を「正式な状態」として確定させる

    重要な設計方針：
    ・state の「唯一の所有者」は GameSession
    ・Graph（GMGraph / PlayerGraph）は state を保持しない
    ・Graph は常に「与えられた state を加工して返す」だけ
    ・将来的に Redis / DB に state を永続化する場合も、
      差し替え先はこの GameSession のみ
    """

    def __init__(
        self,
        *,
        definition: GameDefinition,
        world_state: WorldState,
        player_states: Dict[PlayerName, PlayerState],
        controllers: dict[PlayerName, PlayerController],
        assigned_roles: Dict[PlayerName, RoleName],
        gm_graph: GMGraph,
        gm_internal: GMInternalState,
    ):
        self.definition = definition
        # このゲームのルール定義。
        # 役職構成・フェーズ構成・勝利条件など、
        # 「ゲームが始まる前に確定し、途中で変化しない情報」を持つ。
        #
        # GameSession / GMGraph の判断基準として参照されるが、
        # ゲーム中に書き換えられることは想定しない（immutable）。
        self.world_state = world_state
        # GM（進行役）が管理する「公開状態」。
        #
        # - 現在のフェーズ
        # - 参加プレイヤー一覧
        # - 公開イベント履歴
        #
        # など、「全プレイヤーが共通で認識してよい事実」のみを含む。
        # 役職や陣営などの非公開情報は絶対に含めない。
        self.player_states = player_states
        # 各プレイヤーが内部に持つ状態（内面）。
        #
        # - 自分の役職（真実 or 推測）
        # - 他プレイヤーへの疑念・推論
        # - 過去のイベントの記憶
        #
        # PlayerGraph の入力・出力として更新される。
        # GM は中身を解釈せず、「渡す・受け取る・保存する」だけに留める。
        self.controllers = controllers
        # 各プレイヤーに対応する Controller。
        #
        # - 人間プレイヤー用 Controller
        # - AI プレイヤー用 Controller
        #
        # の違いを吸収するための層。
        # GameSession は「どうやって考えるか」を一切知らない。
        self.assigned_roles = assigned_roles
        ## 各プレイヤーに割り当てられた実際の役職。
        #
        # これは GM（裁定者）だけが知る「真実情報」であり、
        # - 夜行動の解決
        # - 勝敗判定
        #
        # にのみ使用される。
        # 議論フェーズや WorldState / PlayerState に
        # 決して直接流出させてはならない。
        self.gm_graph = gm_graph
        # GMGraph（進行役の思考エンジン）。
        #
        # WorldState を入力として受け取り、
        # 次に起こすべき GameDecision（イベント生成・行動要求など）
        # を決定する。
        #
        # state 自体は保持せず、常に GameSession から渡される。
        self.gm_internal = gm_internal
        # GMInternalState（GMGraph 専用の内部進行状態）。
        #
        # WorldState には含められない、
        # 「進行管理のためだけに必要な非公開情報」を保持する。

        # --- 責務委譲先のインスタンス ---
        self._action_resolver = ActionResolver(assigned_roles=assigned_roles)
        self._dispatcher = Dispatcher()
        self._phase_runner = PhaseRunner()

    @classmethod
    def create(cls, definition: GameDefinition) -> "GameSession":
        """
        ゲーム開始時の GameSession を生成するファクトリメソッド。

        このメソッドの責務：
        - プレイヤー生成
        - 役職割り当て
        - PlayerState の初期化
        - WorldState の初期化

        重要な設計意図：
        ・GameSession はこのメソッド経由でのみ生成する
        ・初期化手順を 1 箇所に集約する
        ・外部から GameSession を直接 new させない
        """

        players, assigned_roles, player_memories, controllers = setup_game(definition)
        # ゲーム定義に基づいて初期セットアップを行う。
        #
        # - players: プレイヤー一覧
        # - assigned_roles: 各プレイヤーの真の役職
        # - player_memories: 各プレイヤーの初期記憶
        # - controllers: 各プレイヤーに対応する Controller

        # ゲーム開始時の WorldState を生成。
        #
        # ワンナイト人狼では必ず definition.phases の先頭（night）から始まる。
        # public_events はまだ何も起きていないため空。
        world_state = WorldState(
            phase=definition.phases[0],
            players=players,
            public_events=[],
        )

        # PlayerMemory を PlayerState にラップする
        #
        # input / output は LangGraph 実行時に
        # 毎ターン上書きされるため、ここでは初期値を与えるのみ。
        from src.core.types.player import PlayerInternalState

        player_states = {
            player: PlayerState(
                memory=memory,
                input=PlayerInput(),
                output=None,
                internal=PlayerInternalState(),
            )
            for player, memory in player_memories.items()
        }

        # GMInternalState は GMGraph が進行管理のためにのみ使用する内部状態。
        # WorldState とは異なり、プレイヤーからは観測されない。
        #
        # night_pending:
        # - 夜フェーズ中に「まだ行動を完了していないプレイヤー集合」
        # - 初期状態では全員が未完了のため、players 全員をセットする
        # - PlayerOutput が解決されるたびに該当プレイヤーを除外していく想定
        gm_internal = GMInternalState(
            night_pending=set(players),
            vote_pending=list(players),
            gm_event_cursor=0,
        )

        # 初期化済みの要素をすべて束ねて GameSession を生成する
        return cls(
            definition=definition,
            world_state=world_state,
            player_states=player_states,
            controllers=controllers,
            assigned_roles=assigned_roles,
            gm_graph=gm_graph,
            gm_internal=gm_internal,
        )

    def run_player_turn(
        self,
        *,
        player: PlayerName,
        input: PlayerInput,
    ) -> PlayerOutput | None:
        """
        GM からの PlayerRequest / Event を受け取り、
        対象プレイヤーの次の状態を計算し、出力を返す。

        - input はターン限定の刺激（このターンにのみ有効）
        - output はターン限定の結果（次ターンには持ち越さない）
        - state の所有・永続的な更新は GameSession の責務
        """

        # 現在のプレイヤー状態（確定済み・永続）
        old_state = self.player_states[player]

        # このプレイヤーに対応する Controller
        # （人間 / AI / テスト用などの差異を吸収）
        controller = self.controllers[player]

        # --- 待機ターン判定 ---
        # request も event も無い場合は
        # 「このターンは何も観測も行動も発生しない」
        # ため、state を一切変更せず終了する
        if input.request is None and input.event is None:
            return None

        # --- Controller 用の working state を作成 ---
        # Controller / PlayerGraph は state の所有者ではないため、
        # 既存 state を直接渡さず、必ずコピーを渡す
        working_state = deepcopy(old_state)

        # 今ターンに GM から与えられた入力を注入
        # （イベント通知 / 行動要求）
        working_state["input"] = input
        
        # ゲーム定義を注入（PlayerGraph から参照可能にするため）
        # ※ PlayerState の型には含まれていないが、動的に注入する
        working_state["game_def"] = self.definition

        # 出力はこのターン用に初期化
        # PlayerGraph がここに結果を書き込む
        working_state["output"] = None

        # --- 次の状態を計算 ---
        # Controller（内部で PlayerGraph を使用）が
        # working_state をもとに次の状態を生成する
        new_state = controller.act(state=working_state)

        # --- 結果の確定保存 ---
        # 計算された state を正式な状態として保存
        # （state の確定・永続化は GameSession の責務）
        self.player_states[player] = new_state

        # このターンで生成された出力のみを返す
        # （無い場合は None）
        return new_state["output"]

    def run_gm_step(self) -> GMGraphState:
        """
        GMGraph を 1 ステップだけ実行するための最小単位メソッド。

        - GMGraph が正しく invoke できるかを確認する目的
        - この時点では Player への dispatch（行動要求の配布）は行わない
        - world_state の確定保存は GameSession の責務
        """

        # --- GMGraph に渡す state を構築 ---
        # world_state:
        #   現在のゲームの公開状態（事実）
        #   ※ GameSession が所有し、GMGraph は直接は保持しない
        #
        # decision:
        #   このステップ中に GM が下す判断を格納する作業領域
        #   （イベント生成・行動要求など）
        gm_graph_state = GMGraphState(
            world_state=self.world_state,
            decision=GameDecision(),
            internal=self.gm_internal,
            game_def=self.definition,
            assigned_roles=self.assigned_roles,
        )

        # --- GMGraph を 1 ステップ実行 ---
        # world_state を参照しながら判断を行い、
        # 必要に応じて world_state の更新案や decision を生成する
        gm_graph_state = self.gm_graph.invoke(gm_graph_state)

        # --- world_state の確定保存 ---
        # GMGraph が返した最新の world_state を
        # GameSession が「正式な状態」として確定させる
        # （state の所有者は常に GameSession）
        self.world_state = gm_graph_state["world_state"]

        # --- 実行結果を返却 ---
        # decision は後続の dispatch 処理やデバッグ・テストで利用される
        return gm_graph_state

    # =========================================================
    # 委譲メソッド（Dispatcher）
    # =========================================================

    def dispatch(self, decision: GameDecision) -> None:
        """
        GMGraph から返された GameDecision を受け取り、
        実際のゲーム世界（WorldState / PlayerState）に反映する。

        この実装は Dispatcher クラスに委譲する。
        """
        self._dispatcher.dispatch(decision, session=self)

    # =========================================================
    # 委譲メソッド（ActionResolver）
    # =========================================================

    def resolve_player_output(
        self,
        *,
        player: PlayerName,
        output: PlayerOutput,
    ) -> None:
        """
        PlayerGraph / Controller が返した PlayerOutput を解釈し、
        ゲーム世界（WorldState / PlayerState）に副作用として反映する。

        この実装は ActionResolver クラスに委譲する。
        """
        self._action_resolver.resolve(
            player=player,
            output=output,
            session=self,
        )

    # =========================================================
    # 委譲メソッド（PhaseRunner）
    # =========================================================

    def run_night_phase(self) -> None:
        """
        夜フェーズを実行する。

        この実装は PhaseRunner クラスに委譲する。
        """
        self._phase_runner.run_night_phase(session=self)

    def run_day_step(self) -> None:
        """
        昼フェーズ（議論フェーズ）の 1 ステップを実行する。

        この実装は PhaseRunner クラスに委譲する。
        """
        self._phase_runner.run_day_step(session=self)

    def run_vote_step(self) -> None:
        """
        投票フェーズ（vote フェーズ）の 1 ステップを実行する。

        この実装は PhaseRunner クラスに委譲する。
        """
        self._phase_runner.run_vote_step(session=self)

    def run_result_step(self) -> None:
        """
        結果フェーズ（result フェーズ）の 1 ステップを実行する。

        この実装は PhaseRunner クラスに委譲する。
        """
        self._phase_runner.run_result_step(session=self)
