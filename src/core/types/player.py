"""
プレイヤー関連の型定義

責務:
- プレイヤー識別（PlayerName）
- プレイヤーの内部状態（Memory/State）
- プレイヤーの入出力（Input/Output）
- 能力結果の表現
"""

from typing import List, Dict, Optional, Literal, TypeAlias, TypedDict, Union, Any
from pydantic import BaseModel, Field, model_validator

from src.core.types.roles import RoleName
from src.core.types.events import GameEvent, PlayerRequest, PlayerRequestType
from src.core.memory import (
    Reflection,
    Reaction,
    Strategy,
    StrategyPlan,
    StrategyReview,
    SpeakReview,
    PlayerMilestoneStatus,
    PlayerPolicyWeights,
)
from src.core.memory.speak import Speak

__all__ = [
    "PlayerName",
    "RoleProb",
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
]


# =========================
# プレイヤーを識別するための名前型
# =========================
PlayerName: TypeAlias = str


# =========================
# 役職確率分布（信念モデル）
# =========================
class RoleProb(BaseModel):
    """
    1人のプレイヤーに対する役職確率分布。

    - key   : RoleName
    - value : 確率（0.0〜1.0）
    - 合計は 1.0 でなければならない
    """

    probs: Dict[RoleName, float] = Field(default_factory=dict)
    # 役職ごとの確率分布
    # 例: {"villager": 0.5, "seer": 0.2, "werewolf": 0.3}

    @model_validator(mode="after")
    def validate_probs(self) -> "RoleProb":
        """
        確率分布の妥当性チェック。

        - 確率の総和が 1.0（誤差許容）であること
        - 各確率が 0.0〜1.0 の範囲内であること

        推論・更新ロジックのバグを早期に検出するため、
        モデルレベルで強制する。
        """
        total = sum(self.probs.values())

        # 浮動小数誤差を考慮して ±0.001 まで許容
        if not (0.999 <= total <= 1.001):
            raise ValueError(f"RoleProb total must be 1.0, got {total}")

        for role, p in self.probs.items():
            if p < 0.0 or p > 1.0:
                raise ValueError(f"Invalid probability for {role}: {p}")

        return self


# =========================
# プレイヤーの記憶（内部状態）
# =========================
# プレイヤーAIが内部に保持する「脳の中身」
class PlayerMemory(BaseModel):
    self_name: PlayerName
    # 自分自身のプレイヤー名

    self_role: RoleName
    # 自分の役職（AIは自分の役職を知っている）

    players: list[PlayerName]
    # 全プレイヤー名のリスト

    # =========================
    # 観測した事実（公開情報）
    # =========================
    observed_events: list[GameEvent]
    # public_event を「そのまま」保存
    # 事実のみ・改変禁止

    role_beliefs: Dict[PlayerName, RoleProb]
    """
    各プレイヤーが各役職であると考える確率分布。

    - key   : プレイヤー名
    - value : RoleProb（そのプレイヤーの役職確率分布）

    例:
    {
        "Bob": RoleProb(
            probs={
                "villager": 0.5,
                "seer": 0.2,
                "werewolf": 0.3,
            }
        )
    }

    この構造により、
    - 「Bob は怪しい」という単一ラベルではなく
    - 不確実性を含んだ信念表現が可能になる
    """

    history: List[Reaction | Reflection] = Field(default_factory=list)
    # 観測・推論・内省の履歴ログ
    # - 基本的には GameEvent 相当の dict（発言・投票結果など）
    # - 将来的に自己思考や推論ログも混在する想定

    strategy_plan: Optional[StrategyPlan] = None
    # 長期的な戦略計画（Night Phaseで生成し、ゲーム中保持する）


    log_summary: str = ""
    # 要約済みのログテキスト
    # 差分要約の結果がここに蓄積される

    last_summarized_event_index: int = 0
    # 最後に要約したイベントのインデックス
    # 次回は observed_events[last_summarized_event_index:] を対象とする

    # =========================
    # 可変情報（毎ターン更新）
    # =========================
    milestone_status: Optional[PlayerMilestoneStatus] = None
    # 各マイルストーンの現在の状態
    # 議論フェーズごと、またはターンごとに更新

    policy_weights: Optional[PlayerPolicyWeights] = None
    # milestone_status から動的に算出される発言方針パラメータ
    # speak_generator の入力として利用


# =========================
# プレイヤーへの入力
# =========================
# 外部（GMやゲーム進行）から与えられる刺激
# total=False により、すべてのキーが必須ではない
class PlayerInput(BaseModel):
    event: Optional[GameEvent] = None
    # 起きた出来事（他人の発言、投票結果など）
    # 例: {"type": "speech", "player": "Bob", "text": "..."}

    request: Optional[PlayerRequest] = None
    # 今このプレイヤーが求められている行動
    # 例: {"action": "speak"} / {"action": "vote"}


# =========================
# 能力結果（AbilityResult）
# =========================
# 夜フェーズにおいて「プレイヤーが実行した行動の結果」を表す型群。
class NoAbility(BaseModel):
    """
    行動なしを表す能力結果。

    主に以下の役職で使用される:
    - 村人
    - 狂人（現時点では夜行動を持たない）

    ポイント:
    - 「何も起こらなかった」ことを明示的に表すための型
    - role（役職）そのものを Ability に含めないことで、
      AbilityResult の責務を「行動結果」に限定している
    """

    kind: Literal["none"]


class SeerAbility(BaseModel):
    """
    占い師の夜行動結果。

    - target に指定されたプレイヤーを占った、という事実のみを表す
    - 占い結果（役職の真実）は GM / Session 側で解決される

    注意:
    - ここでは「誰を占ったか」までしか持たない
    - 「占い結果を知った」というイベントは別途 GameEvent として通知される
    """

    kind: Literal["seer"]
    target: PlayerName


# =========================
# AbilityResult 型
# =========================
# 夜フェーズで PlayerGraph が返す「能力使用結果」の共用型。
#
# GM / Session はこの型を解釈し、
# - ゲーム世界への副作用（WorldState 更新）
# - 個別プレイヤーへのイベント通知
# を確定させる。
class WerewolfAbility(BaseModel):
    """
    人狼の夜行動結果。

    - ワンナイト人狼では「何もしない／相談のみ」の場合が多いため、
      現時点では追加情報を持たない
    - 将来、襲撃対象や相談内容を扱う場合はフィールドを拡張する想定
    """

    kind: Literal["werewolf"]


class ThiefAbility(BaseModel):
    """
    怪盗の夜行動結果。

    - target に指定されたプレイヤーと役職を交換した、という事実を表す
    - 実際の交換処理は ActionResolver 側で実行される
    - 交換後、怪盗は相手の役職を持つ（勝利条件も変わる）
    """

    kind: Literal["thief"]
    target: PlayerName


AbilityResult = Union[
    NoAbility,
    SeerAbility,
    WerewolfAbility,
    ThiefAbility,
]


# =========================
# 投票（Vote）
# =========================
class Vote(BaseModel):
    voter: PlayerName
    target: PlayerName


# =========================
# プレイヤーからの出力
# =========================
class PlayerOutput(BaseModel):
    action: PlayerRequestType
    # GM から提示された PlayerRequest に対して、
    # プレイヤー（人間 / AI）が選択した行動の種類
    payload: AbilityResult | dict | None = None
    # 行動に付随する具体的な情報
    # action の種類によって内容が変わる
    #
    # 例:
    # - action == "speak" -> {"message": str}
    # - action == "vote" -> {"target": PlayerName}
    # - action == "use_ability" -> {"target": PlayerName} など


# =========================
# プレイヤーの内部進行状態
# =========================
class PlayerInternalState(BaseModel):
    """
    PlayerGraph 内でのみ使用される一時的な進行状態。

    戦略生成→発言生成→レビューのフローで
    中間状態を保持するために使用する。
    """

    pending_strategy: Optional[Strategy] = None
    # 生成中の戦略（まだ確定していない）

    pending_speak: Optional[Speak] = None
    # 生成中の発言（まだ確定していない）

    last_speak_review: Optional[SpeakReview] = None
    # 最後の発言レビュー結果

    speak_review_count: int = 0
    # 発言レビューの回数（無限ループ防止用）


# =========================
# プレイヤーの状態（State）
# =========================
# LangGraph などでノード間を流れる状態オブジェクト
class PlayerState(TypedDict):
    memory: PlayerMemory
    # プレイヤーの内部状態（長期的に保持される記憶）
    # - 自分の役職
    # - 他プレイヤーへの推測
    # - 過去のイベント履歴 など
    #
    # ※ PlayerGraph が更新し、GM は直接変更しない

    input: PlayerInput
    # GM（ゲーム進行役）から与えられる入力
    # - GameEvent: 世界で起きた事実の通知（内面更新のみ）
    # - PlayerRequest: 今ターンの行動機会の提示
    #
    # ※ request が含まれない場合は「待機状態」を意味する

    output: Optional[PlayerOutput]
    # PlayerGraph が生成する出力（request に対する応答）
    #
    # - input に request がある場合:
    #     -> PlayerOutput が設定されることを期待する
    # - input に request がない場合:
    #     -> None（外界への行動なし）
    #
    # ※ GM は output を解釈・適用する側であり、
    #    output を事前に設定することはない

    internal: PlayerInternalState
    # グラフ内部でのみ使用される一時的な進行状態
    # - 戦略生成・レビューの中間状態
    # - 発言生成・レビューの中間状態
    #
    # ※ グラフ実行終了後にリセットされる想定

    game_def: Any
    # GameSession から動的に注入される GameDefinition
    # 循環参照回避のために Any としているが、実体は GameDefinition
    # プレイヤーロジックがルールを参照するために使用する
