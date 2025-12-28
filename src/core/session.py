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


# =========================
# ゲーム実行セッション
# =========================
# 1 回のゲームを実行するための実行コンテナ。
#
# このクラスは「ゲームという1つの世界」を管理する中心的な存在であり、
# 以下の役割を持つ：
#
# - WorldState / PlayerState / 真実情報（役職）を保持する
# - GMGraph と PlayerGraph の実行を仲介・調停する
# - Graph が返した結果を「正式な状態」として確定させる
#
# 重要な設計方針：
# ・state の「唯一の所有者」は GameSession
# ・Graph（GMGraph / PlayerGraph）は state を保持しない
# ・Graph は常に「与えられた state を加工して返す」だけ
# ・将来的に Redis / DB に state を永続化する場合も、
#   差し替え先はこの GameSession のみ
class GameSession:
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

        # PlayerMemory を PlayerState にラップする
        #
        # input / output は LangGraph 実行時に
        # 毎ターン上書きされるため、ここでは初期値を与えるのみ。
        player_states = {
            player: PlayerState(
                memory=memory,
                input=PlayerInput(),
                output=None,
            )
            for player, memory in player_memories.items()
        }

        # ゲーム開始時の WorldState を生成。
        #
        # ワンナイト人狼では必ず night フェーズから始まる想定。
        # public_events はまだ何も起きていないため空。
        world_state = WorldState(
            phase="night",
            players=players,
            public_events=[],
        )

        # GMInternalState は GMGraph が進行管理のためにのみ使用する内部状態。
        # WorldState とは異なり、プレイヤーからは観測されない。
        #
        # night_pending:
        # - 夜フェーズ中に「まだ行動を完了していないプレイヤー集合」
        # - 初期状態では全員が未完了のため、players 全員をセットする
        # - PlayerOutput が解決されるたびに該当プレイヤーを除外していく想定
        gm_internal = GMInternalState(
            night_pending=set(players),
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

    def dispatch(self, decision: GameDecision) -> None:
        """
        GMGraph から返された GameDecision を受け取り、
        実際のゲーム世界（WorldState / PlayerState）に反映する。

        設計方針:
        - GameDecision は「判断結果」のみを表し、副作用は持たない
        - この dispatch が state を更新する唯一の場所（state の所有者）
        - event と request は同時には来ない運用とする
          （= 観測フェーズと行動フェーズは明確に分離される）
        """
        # =========================================================
        # 1. event の配布（すでに起きた事実の通知）
        # =========================================================
        # - 全プレイヤーに共有される「確定した出来事」
        # - プレイヤーは思考・記憶更新のみを行う（行動はしない）
        # - request と同一 step で同時に存在してよい
        if decision.events:
            for event in decision.events:
                for player in self.player_states:
                    # event は「観測情報」なので全員に配布する
                    self.run_player_turn(
                        player=player,
                        input=PlayerInput(event=event),
                    )
            # event は全員に配布し終えた後で、
            # 公開ログ（WorldState）として確定させる
            self.world_state.public_events.extend(decision.events)
            # GM がどこまで event を配布し終えたかを示すカーソル
            # （LangGraph 実装や再実行・再開時の安全装置として有用）
            self.gm_internal.gm_event_cursor = len(self.world_state.public_events)

        # =========================================================
        # 2. request の配布（今ターンの行動要求）
        # =========================================================
        # - 特定のプレイヤーにのみ送られる
        # - 実際の行動（発言・投票・夜行動など）を発生させる
        # - event と同一 step で同時に存在してよい
        if decision.requests:
            for player, request in decision.requests.items():
                output = self.run_player_turn(
                    player=player,
                    input=PlayerInput(
                        request=request,
                    ),
                )
                # Player の出力（発言・投票・能力使用など）を
                # GM 視点で解釈・確定させ、世界状態に反映する
                #
                # ここで初めて「行動の結果」が事実になる
                self.resolve_player_output(
                    player=player,
                    output=output,
                )

        # =========================================================
        # 3. フェーズ遷移
        # =========================================================
        # - event / request の処理がすべて完了した後に実行される
        # - フェーズ自体は「進行状態」であり、
        #   event（出来事）とは区別して WorldState に直接反映する
        if decision.next_phase is not None:
            self.world_state.phase = decision.next_phase

    def resolve_player_output(
        self,
        *,
        player: PlayerName,
        output: PlayerOutput,
    ) -> None:
        """
        PlayerGraph / Controller が返した PlayerOutput を解釈し、
        ゲーム世界（WorldState / PlayerState）に副作用として反映する。

        このメソッドの位置づけ:
        - 「行動の意味づけ（解釈）」と「副作用の確定」を担う
        - PlayerGraph / PlayerController 自体は副作用を一切持たない
        - GameSession が state の唯一の所有者である、という設計を守るため、
          実際の状態更新は必ずここを経由する

        設計上の重要な前提:
        - output.action は GMGraph / PlayerGraph 側で正規化された値である
        - このメソッドが呼ばれる時点で、
          ・誰が行動したか（player）
          ・どんな行動を選んだか（output）
          が確定している
        - 行動の成否判定・影響範囲の決定はこの層で行う

        拡張方針:
        - 新しい行動を追加する場合は、
          1. PlayerOutput.action に値を追加
          2. この resolve_* メソッドを追加
          3. ここに分岐を追加
        - if/elif が肥大化した場合は
          action -> handler のディスパッチテーブル化も検討可能
        """
        # =========================================================
        # 各 action ごとの解釈・副作用の確定
        # =========================================================
        if output.action == "use_ability":
            print("use_ability")
        elif output.action == "speak":
            self.resolve_speak(player, output)
        elif output.action == "vote":
            self.resolve_vote(player, output)
        elif output.action == "divine":
            self.resolve_divine(player, output)
        else:
            raise ValueError(f"Unknown action: {output.action}")

    def run_night_phase(self) -> None:
        # --- 夜フェーズの進行を 1 ステップ実行 ---
        # 現在の world_state を元に GMGraph を実行し、
        # 夜フェーズで発生すべき「判断結果（decision）」を生成させる
        gm_graph_state = self.run_gm_step()

        # --- GM の判断結果を実行フェーズに反映 ---
        # ・events  : 全プレイヤーに共有される出来事（記憶・推論用）
        # ・requests: 特定プレイヤーへの行動要求
        # Session が state の所有者として、副作用を伴う処理をここで確定させる
        self.dispatch(gm_graph_state["decision"])

        # --- 夜フェーズ固有の完了処理 ---
        # 夜フェーズでは、
        # ・全ての request が処理された時点でフェーズが確定する
        # ・フェーズ遷移の確定は GMGraph ではなく Session の責務
        self.world_state.phase = "day"

    def run_day_step(self) -> None:
        """
        昼フェーズ（議論フェーズ）の 1 ステップを実行する。

        このメソッドの責務:
        - 現在の WorldState を元に GMGraph を 1 回だけ実行する
        - GMGraph が返した GameDecision を dispatch して確定反映する

        設計上の重要な前提:
        - このメソッドは world_state.phase == "day" のときのみ呼ばれる
          （フェーズ判定・制御は呼び出し元の責務）
        - フェーズ遷移（day -> vote など）は GMGraph が
          decision.next_phase に意思として示し、
          実際の更新は dispatch が行う
        - ここではループや待機は行わず、
          常に「1 step = 1 decision」とする

        将来拡張:
        - AI 同士の自動進行では外側でループさせる
        - 人間参加（Web / API）の場合は、
          発言イベントなどを追加した後に 1 回だけ呼び出す
        """
        gm_graph_state = self.run_gm_step()
        self.dispatch(gm_graph_state["decision"])

    def run_vote_step(self) -> None:
        """
        投票フェーズ（vote フェーズ）の 1 ステップを実行する。

        このメソッドの責務:
        - 現在の WorldState を元に GMGraph を 1 回だけ実行する
        - GMGraph が返した GameDecision を dispatch して確定反映する

        設計上の重要な前提:
        - このメソッドは world_state.phase == "vote" のときのみ呼ばれる
        （フェーズ判定・制御は呼び出し元の責務）
        - フェーズ遷移（vote -> result / end など）は GMGraph が
        decision.next_phase に意思として示し、
        実際の更新は dispatch が行う
        - ここではループや待機は行わず、
        常に「1 step = 1 decision」とする

        将来拡張:
        - 人間プレイヤーが投票を入力した後に 1 回だけ呼び出す
        - AI 同士の自動進行では外側でループ制御する
        """
        gm_graph_state = self.run_gm_step()
        self.dispatch(gm_graph_state["decision"])

    def run_result_step(self) -> None:
        """
        結果フェーズ（result フェーズ）の 1 ステップを実行する。

        このメソッドの責務:
        - GMGraph を 1 回だけ実行し、
          勝敗確定・役職公開（reveal）を行う
        - GameDecision を dispatch して最終状態を確定させる

        設計上の前提:
        - world_state.phase == "result" のときのみ呼ばれる
        - result フェーズでは request は一切発生しない
        - decision.next_phase は None（ゲーム終了）
        """
        gm_graph_state = self.run_gm_step()
        self.dispatch(gm_graph_state["decision"])
