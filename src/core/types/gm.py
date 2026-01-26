"""
GM 進行管理の型定義

責務:
- GMの意思決定結果
- GMの内部進行状態
- GMGraph が扱う State
"""

from typing import List, Dict, Optional, TypedDict
from pydantic import BaseModel, Field

from src.core.types.phases import Phase, WorldState, GameDefinition
from src.core.types.events import GameEvent, PlayerRequest
from src.core.types.roles import RoleName, RoleDefinition, Side
from src.core.types.player import PlayerName
from src.core.memory.gm_comment_review import GMCommentReviewResult
from src.core.memory.gm_comment import GMComment
from src.core.memory.gm_plan import GMProgressionPlan

__all__ = [
    "GameDecision",
    "GMInternalState",
    "GMGraphState",
]


# =========================
# GM の意思決定結果
# =========================
# GMGraph が
# 「次にゲームで何を起こすか」
# を判断した結果を表すデータ構造。
#
# これは "状態" ではなく、
# 1 ステップ分の「判断の出力（差分）」。
#
# GameSession がこの Decision を解釈して、
# 実際の状態変更やプレイヤーへの通知を行う。
#
# 典型的な処理フロー:
# 1. GMGraph が GameDecision を生成
# 2. GameSession が
#    - events を public_events に反映
#    - requests を各 PlayerController に dispatch
#    - next_phase を gm_state.phase に反映
class GameDecision(BaseModel):
    events: List[GameEvent] = Field(default_factory=list)
    # 今ターンで新たに確定した「世界で起きた事実」
    #
    # 例:
    # ・夜の能力結果
    # ・誰かの発言
    # ・投票結果
    # ・最終的な役職公開
    #
    # ※ ここに入った時点で「過去の事実」になる

    requests: Dict[PlayerName, PlayerRequest] = Field(default_factory=dict)
    # 各プレイヤーに対する「次の行動要求」
    #
    # 例:
    # {
    #   "Alice": {"request_type": "speak", "payload": {...}},
    #   "Bob":   {"request_type": "wait",  "payload": {}},
    # }
    #
    # ※ GM は直接行動を実行しない
    # ※ あくまで「行動機会」を与えるだけ

    next_phase: Optional[Phase] = None
    # 次に遷移するフェーズ
    #
    # 例:
    # - "night" -> "day"
    # - "day"   -> "vote"
    # - "vote"  -> "reveal"
    #
    # None の場合:
    # ・フェーズ継続
    # ・または GameSession 側で遷移制御


class GMInternalState(BaseModel):
    """
    GMGraph が内部的に保持する進行管理用の State。

    この State は「ゲーム世界の事実」ではなく、
    GM がフェーズ進行・待機管理を行うための補助情報を表す。

    設計上の位置づけ:
    - WorldState には含めない（＝プレイヤーからは観測不能）
    - PlayerGraph には一切渡らない
    - GMGraph のローカルな思考・制御用 State

    主な用途:
    - 夜フェーズで「まだ行動を返していないプレイヤー」の管理
    - 全員の行動完了を検知して次フェーズへ遷移する判断材料
    """

    night_started: bool = False
    # 夜フェーズ開始を示すフラグ

    day_started: bool = False
    # 日フェーズ開始を示すフラグ

    vote_started: bool = False
    # 投票フェーズ開始を示すフラグ

    night_pending: list[PlayerName]
    # 夜フェーズにおいて、まだ行動を完了していないプレイヤー集合
    #
    # 例:
    # - 夜開始時: 全プレイヤーが含まれる
    # - 各 PlayerOutput を処理するたびに該当プレイヤーを削除
    # - 空集合になったら「夜フェーズ完了」と判断可能
    #
    # 重要:
    # ・役職や行動内容はここには含めない
    # ・あくまで「進行管理」のみを目的とする

    vote_pending: list[PlayerName]
    # 投票フェーズにおいて、まだ投票していないプレイヤー集合
    #
    # 例:
    # - 投票開始時: 全プレイヤーが含まれる
    # - 各 PlayerOutput を処理するたびに該当プレイヤーを削除
    # - 空集合になったら「投票完了」と判断可能
    #
    # 重要:
    # ・役職や行動内容はここには含めない
    # ・あくまで「進行管理」のみを目的とする

    votes: Dict[PlayerName, PlayerName] = Field(default_factory=dict)
    # 投票結果の集計用
    # { "投票者": "投票先" }

    discussion_turn: int = 0  # 発言回数
    max_discussion_turn: int = 30  # 上限
    min_discussion_turn: int = 10  # 下限

    gm_event_cursor: int = 0
    # GM が public_events をどこまで処理したかを示すカーソル
    #
    # 用途:
    # ・GMGraph が「未処理の公開イベント」を検出するため
    # ・イベントの二重処理を防ぐため
    #
    # 設計意図:
    # ・WorldState 自体は履歴をすべて保持する
    # ・「どこまで見たか」は cursor で管理することで
    #   再実行・デバッグ・リプレイ耐性を高める
    pending_gm_comment: Optional[GMComment] = None

    last_gm_review: Optional[GMCommentReviewResult] = None

    gm_comment_review_count: int = 0

    log_summary: str = ""
    # 要約済みのログテキスト

    last_summarized_event_index: int = 0
    # 最後に要約したイベントのインデックス

    progression_plan: Optional[GMProgressionPlan] = None
    # ゲーム全体の進行計画（夜フェーズで生成）


# =========================
# GMGraph が扱う State
# =========================
# GMGraph 内部で使用される合成 State。
#
# ・world_state  : すでに確定した「過去と現在の事実」
# ・decision  : 今ステップで導き出された「判断結果」
#
# 重要:
# ・world_state は原則 immutable として扱う
# ・decision は一時的な working memory
# ・最終的な state 更新は GameSession の責務
class GMGraphState(TypedDict):
    world_state: WorldState
    # 確定済みのゲーム状態（事実）
    # GMGraph はこれを「読む」ことが主

    decision: GameDecision
    # GMGraph がこのステップで生成する判断結果
    # 次の状態遷移の材料

    internal: GMInternalState
    # GMGraph の内部進行状態
    #
    # 特徴:
    # ・ゲーム世界の事実ではない
    # ・プレイヤーには一切公開されない
    # ・GMGraph がフェーズ制御を行うための補助情報
    #
    # 例:
    # ・夜フェーズの未完了プレイヤー管理
    # ・将来的な「タイムアウト」「自動スキップ」判定

    game_def: GameDefinition
    # ゲームの定義情報（役職構成など）
    # GM は個別の役職割り当てを知らず、この定義と公開イベントのみから判断を行う。

    assigned_roles: Dict[PlayerName, RoleName]
    # 【追加】GM のみが知る真実の役職割り当て。
    # Result フェーズで勝敗判定を行うために必要。
    # 通常の思考プロセスでは（公平性のため）参照すべきではないが、
    # システム的な正解判定のために State に含める。
