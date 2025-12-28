"""
プレイヤー関連の型定義

責務:
- プレイヤー識別（PlayerName）
- プレイヤーの内部状態（Memory/State）
- プレイヤーの入出力（Input/Output）
- 能力結果の表現
"""

from typing import List, Dict, Optional, Literal, TypeAlias, TypedDict, Union
from pydantic import BaseModel

from src.core.types.roles import RoleName
from src.core.types.events import GameEvent, PlayerRequest, PlayerRequestType

__all__ = [
    "PlayerName",
    "PlayerMemory",
    "PlayerInput",
    "PlayerOutput",
    "PlayerState",
    "NoAbility",
    "SeerAbility",
    "WerewolfAbility",
    "AbilityResult",
]


# =========================
# プレイヤーを識別するための名前型
# =========================
PlayerName: TypeAlias = str


# =========================
# プレイヤーの記憶（内部状態）
# =========================
# プレイヤーAIが内部に保持する「脳の中身」
class PlayerMemory(BaseModel):
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


class NoAbility(BaseModel):
    kind: Literal["none"]


class SeerAbility(BaseModel):
    kind: Literal["seer"]
    target: PlayerName


class WerewolfAbility(BaseModel):
    kind: Literal["werewolf"]


AbilityResult = Union[
    NoAbility,
    SeerAbility,
    WerewolfAbility,
]


# =========================
# プレイヤーからの出力
# =========================
class PlayerOutput(BaseModel):
    action: PlayerRequestType
    # GM から提示された PlayerRequest に対して、
    # プレイヤー（人間 / AI）が選択した行動の種類
    payload: AbilityResult | None = None
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

