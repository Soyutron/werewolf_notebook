"""
イベント・リクエスト関連の型定義

責務:
- ゲーム内で発生するイベント（事実）の表現
- GMからプレイヤーへの行動要求の表現
"""

from typing import Literal
from pydantic import BaseModel

__all__ = [
    "GameEventType",
    "GameEvent",
    "PlayerRequestType",
    "PlayerRequest",
]


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
    "night_started",  # 夜フェーズ開始
    "night_action",  # 夜に能力が使われた（占い・役職確認など）
    "divine_result",  # 占い結果
    "role_swapped",  # 怪盗による役職交換結果
    "day_started",  # 昼フェーズ開始
    "gm_comment",  # GMコメント
    "speak",  # 誰かが発言した（昼フェーズの会話ログ）
    "vote_started",  # 投票フェーズ開始
    "vote",  # 投票が行われた（誰が誰に投票したか）
    "reveal",  # 全役職公開（ゲーム終了・勝敗確定）
    "phase_start",  # フェーズ開始
    "game_end",  # ゲーム終了（勝者と結果の詳細）
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
class GameEvent(BaseModel):
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
class PlayerRequest(BaseModel):
    request_type: PlayerRequestType
    # 求められている行動の種類

    payload: dict
    # 行動に必要な補足情報
    # 例:
    # - use_ability: {"candidates": ["Bob", "Charlie"]}
    # - speak: {"topic": "who_is_werewolf"}
    # - vote: {"candidates": ["Alice", "Bob", "Charlie"]}
