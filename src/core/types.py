from typing import TypedDict, List, Dict, Optional, Literal, TypeAlias

# =========================
# 役職名・陣営名を Literal で固定
# =========================

RoleName = Literal[
    "villager",  # 村人：特殊能力を持たない基本役職
    "werewolf",  # 人狼：村を欺く敵陣営
    "seer",  # 占い師：夜に役職を確認できる
    "madman",  # 狂人：勝利条件は人狼側だが、占い判定カテゴリは人間
]

# =========================
# 陣営（Side）の定義
# =========================
# ゲームにおける「陣営」を表す共通カテゴリ
# ・昼フェーズでの立場（DaySide）
# ・最終的な勝利条件の帰属（WinSide）
# の両方で使用される
Side = Literal[
    "village",
    "werewolf",
]

# =========================
# 昼の議論・投票構造における立場
# =========================
# 「昼フェーズでどちら側として扱われるか」を表す
# ・投票
# ・人数カウント
# ・発言上の立場
# に影響する
DaySide = Side

# =========================
# 勝利条件の帰属先
# =========================
# 「どちらの勝利条件を満たしたときに自分も勝利になるか」
# ・最終的な勝敗判定にのみ使用
# ・昼の立場や正体とは独立
WinSide = Side


# =========================
# 役職（Role）の定義
# =========================
# 1つの役職が持つべき情報を定義する
class RoleDefinition(TypedDict):
    name: RoleName  # 役職名（例: "villager", "werewolf"）
    day_side: DaySide  # 昼の立場
    win_side: WinSide  # 勝利条件の帰属
    # NOTE:
    # - day_side は「昼フェーズでの扱い」を表す
    # - win_side は「最終勝敗判定のみ」に使用される
    # - 両者は一致するとは限らない（例: madman）


# =========================
# ゲーム進行フェーズ（ワンナイト人狼）
# =========================
# ワンナイト人狼では
# ・夜フェーズは1回のみ（役職能力の実行）
# ・昼フェーズは1回のみ（議論）
# ・投票は1回のみで、結果が出た時点でゲーム終了
# となるため、フェーズは最小限の3つに絞っている
Phase = Literal[
    "night",  # 夜：占い師などの役職能力を実行するフェーズ
    "day",  # 昼：全プレイヤーが発言・議論を行うフェーズ
    "vote",  # 投票：1回のみ行い、吊られた役職で勝敗が決定する
]


# =========================
# ゲーム全体の定義
# =========================
# このゲームがどんな構成・ルールを持つかを表す
class GameDefinition(TypedDict):
    roles: Dict[RoleName, RoleDefinition]
    # 役職名 -> RoleDefinition の対応表

    role_distribution: List[RoleName]
    # 各プレイヤーに配られる役職の一覧
    # 例: ["villager", "villager", "seer", "werewolf"]

    phases: List[Phase]
    # ゲーム進行フェーズ
    # 例: ["night", "day", "vote"]


# プレイヤーを識別するための名前型
PlayerName: TypeAlias = str


# =========================
# プレイヤーの記憶（内部状態）
# =========================
# プレイヤーAIが内部に保持する「脳の中身」
class PlayerMemory(TypedDict):
    self_name: PlayerName
    # 自分自身のプレイヤー名

    self_role: RoleName
    # 自分の役職（AIは自分の役職を知っている）

    beliefs: Dict[PlayerName, RoleName | Literal["unknown"]]
    # 他プレイヤーの「現在もっともそれらしい役職」の推測
    #
    # ・現段階では「最尤の役職」だけを保持する簡易表現
    # ・確証が持てない場合は "unknown" を入れる
    #
    # 将来的な拡張案:
    # - 各役職の確率分布を保持する形式に拡張する想定
    #   例: Dict[player, Dict[RoleName, float]]
    #
    # 例（現在）:
    # {"Bob": "villager", "Charlie": "werewolf"}
    #
    # 例（将来）:
    # {"Bob": {"villager": 0.6, "seer": 0.2, "werewolf": 0.2}}

    suspicion: Dict[PlayerName, float]
    # 他プレイヤーが「敵陣営（人狼側）である可能性」の強さ
    #
    # ・現段階では「人狼である疑い」を 1 次元の数値で表現
    # ・役職の違い（占い師・狂人など）は直接は区別しない
    #
    # スケール定義:
    # 0.0 = 完全に白（人狼である可能性がほぼない）
    # 0.5 = 中立
    # 1.0 = ほぼ黒（人狼である可能性が非常に高い）
    #
    # 将来的な拡張案:
    # - 陣営ごとの確率（village / werewolf）に分解
    # - beliefs（役職分布）から派生的に計算する設計も想定

    history: List[dict]
    # 観測・推論・内省の履歴ログ
    # - 基本的には GameEvent 相当の dict（発言・投票結果など）
    # - 将来的に自己思考や推論ログも混在する想定


# =========================
# ゲーム内イベントの種類
# =========================
# GM（ゲーム進行）によって発生した「世界で起きた事実」を表す
# プレイヤーAIはこれを受け取り、記憶更新や推論に利用する
#
# ※ ワンナイト人狼では
#   夜 → 議論 → 投票 → 結果公開
#   の最小構成のみを定義している
GameEventType = Literal[
    "night_action",  # 夜に能力が使われた（占い・役職確認など）
    "speech",  # 誰かが発言した（昼フェーズの会話ログ）
    "vote",  # 投票が行われた（誰が誰に投票したか）
    "reveal",  # 全役職公開（ゲーム終了・勝敗確定）
]

# =========================
# プレイヤーへの行動要求の種類
# =========================
# GM からプレイヤー（人間 / AI）に対して
# 「今この行動をしてください」と求める内容を表す
#
# ※ request は「命令」ではなく「行動機会の提示」
# ※ request が送られない場合は、待機状態を意味する
PlayerRequestType = Literal[
    "use_ability",  # 夜フェーズ：能力を使う（使わない選択も含む）
    "speak",  # 昼フェーズ：発言する
    "vote",  # 投票フェーズ：投票先を選ぶ
]


# =========================
# ゲームイベント
# =========================
# すでに発生した出来事を表すデータ構造
# ・GM が生成する
# ・全プレイヤーに共有される
# ・プレイヤーの memory / history に蓄積される
class GameEvent(TypedDict):
    event_type: GameEventType
    # イベントの種類（発言・夜行動・投票・結果公開）

    payload: dict
    # イベント固有の情報
    # 例:
    # - speech: {"player": "Alice", "text": "..."}
    # - night_action: {"actor": "Seer", "target": "Bob"}
    # - vote: {"voter": "Alice", "target": "Bob"}
    # - reveal: {"roles": {...}}


# =========================
# プレイヤーへの行動要求
# =========================
# GM が特定のプレイヤーに対して
# 「次に何をするべきか」を伝えるためのデータ構造
#
# ・未来の行動を指示する
# ・GameEvent（過去の事実）とは明確に区別される
class PlayerRequest(TypedDict):
    request_type: PlayerRequestType
    # 求められている行動の種類

    payload: dict
    # 行動に必要な補足情報
    # 例:
    # - use_ability: {"candidates": ["Bob", "Charlie"]}
    # - speak: {"topic": "who_is_werewolf"}
    # - vote: {"candidates": ["Alice", "Bob", "Charlie"]}


# =========================
# プレイヤーへの入力
# =========================
# 外部（GMやゲーム進行）から与えられる刺激
# total=False により、すべてのキーが必須ではない
class PlayerInput(TypedDict, total=False):
    event: GameEvent
    # 起きた出来事（他人の発言、投票結果など）
    # 例: {"type": "speech", "player": "Bob", "text": "..."}

    request: PlayerRequest
    # 今このプレイヤーが求められている行動
    # 例: {"action": "speak"} / {"action": "vote"}


# =========================
# プレイヤーからの出力
# =========================
class PlayerOutput(TypedDict):
    action: PlayerRequestType
    # GM から提示された PlayerRequest に対して、
    # プレイヤー（人間 / AI）が選択した行動の種類
    payload: dict
    # 行動に付随する具体的な情報
    # action の種類によって内容が変わる
    #
    # 例:
    # - action == "speak" -> {"message": str}
    # - action == "vote" -> {"target": PlayerName}
    # - action == "use_ability" -> {"target": PlayerName} など


# =========================
# プレイヤーの状態（State）
# =========================
# LangGraph などでノード間を流れる状態オブジェクト
class PlayerState(TypedDict):
    memory: PlayerMemory
    # 長期的に保持される記憶（思考・推論の基盤）

    input: PlayerInput
    # 今ターンで受け取った入力（イベント / リクエスト）

    output: Optional[PlayerOutput]
    # プレイヤーが出力した行動
    # 例: {"message": "..."} / {"vote": "..."}
    # 行動しない場合は None
