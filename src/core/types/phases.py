"""
フェーズ・ゲーム定義・ワールド状態の型定義

責務:
- ゲーム進行フェーズの定義
- ゲーム全体のルール定義
- ワールド状態（公開状態）の表現
- ゲーム結果の表現
"""

from typing import List, Dict, Literal, Optional
from pydantic import BaseModel

from src.core.types.roles import RoleName, RoleDefinition, Side
from src.core.types.player import PlayerName
from src.core.types.events import GameEvent

__all__ = [
    "Phase",
    "GameDefinition",
    "WorldState",
    "GameResult",
    "get_next_phase",
]


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
    "result",
]


# =========================
# ゲーム全体の定義
# =========================
# このゲームがどんな構成・ルールを持つかを表す
class GameDefinition(BaseModel):
    roles: Dict[RoleName, RoleDefinition]
    # 役職名 -> RoleDefinition の対応表

    role_distribution: List[RoleName]
    # 各プレイヤーに配られる役職の一覧
    # 例: ["villager", "villager", "seer", "werewolf"]

    phases: List[Phase]
    # ゲーム進行フェーズ
    # 例: ["night", "day", "vote"]


class GameResult(BaseModel):
    """
    ゲーム終了時に確定・公開される最終結果。

    設計上の位置づけ:
    - phase == "result" のときのみ意味を持つ
    - ゲーム中は WorldState.result は常に None
    - WorldState の中で唯一「役職」を公開する例外的な構造

    注意:
    - ゲーム進行中の思考・判断には一切使用しない
    - PlayerGraph は result フェーズでのみ参照する想定
    """

    winner: Side
    # 勝利した陣営
    # 例: "village", "werewolf"

    executed_players: List[PlayerName]
    # 最終的に処刑（または敗北条件に関与）したプレイヤー
    # ワンナイト人狼等で処刑が存在しない場合は空リスト
    
    roles: dict[PlayerName, RoleName]
    # 全プレイヤーの最終役職一覧（完全公開）
    # result フェーズでのみ公開される


# =========================
# GM が管理する進行状態
# =========================
# GM（進行役）がイベント駆動で管理するゲーム全体の「公開状態」。
#
# この State は、
# - ゲームが今どこまで進んでいるか
# - 全プレイヤーが共通で認識してよい事実
# のみを保持する。
#
# 重要な設計方針:
# ・GMGraph / GameSession が参照・更新する
# ・PlayerGraph からも「観測可能な世界」として参照されうる
# ・役職・陣営などの非公開情報は一切含めない
#   （公平性・情報非対称性を保つため）
#
# つまり WorldState は
# 「全員が同じものを見てよい世界の状態」
# を表す。
class WorldState(BaseModel):
    phase: Phase
    # 現在のゲーム進行フェーズ
    # GM の進行判断の基準となる
    #
    # 例:
    # - "night"   : 夜フェーズ（能力使用）
    # - "day"     : 昼フェーズ（議論）
    # - "vote"    : 投票フェーズ
    # - "result"  : 結果フェーズ

    players: List[PlayerName]
    # このゲームに参加している全プレイヤーの一覧
    #
    # 用途:
    # ・発言順 / 投票順の決定
    # ・全体人数の把握
    #
    # ※ 原則としてゲーム中は不変（immutable）想定

    public_events: List[GameEvent]
    # 全体に公開された出来事の履歴
    #
    # 含まれるものの例:
    # ・誰かの発言
    # ・投票結果
    # ・フェーズ遷移
    # ・ゲーム終了時の公開情報
    #
    # 用途:
    # ・PlayerMemory への入力
    # ・フロントエンド表示
    # ・ログ / リプレイ再生
    #
    # ※ GM が確定させた「過去の事実」のみを格納する

    pending_events: list[GameEvent] = []
    # 確定したが、まだ配布されていない公開イベント

    result: GameResult | None = None
    # ゲームの最終結果
    #
    # ・ゲーム進行中は常に None
    # ・phase == "result" になったタイミングで設定される
    #
    # WorldState の原則（非公開情報を持たない）の例外だが、
    # 「結果公開フェーズ」でのみ全情報を解禁するため問題ない


# =========================
# ヘルパー関数
# =========================

def get_next_phase(current_phase: Phase, definition: GameDefinition) -> Optional[Phase]:
    """
    GameDefinition に基づいて次のフェーズを取得する。

    Args:
        current_phase: 現在のフェーズ
        definition: ゲーム定義（phases リストを含む）

    Returns:
        次のフェーズ。
        - 定義された最後のフェーズの次は "result" を返す（まだ result でなければ）。
        - "result" の次は None を返す。
        - 定義に含まれないフェーズの場合は None を返す。
    """
    if current_phase == "result":
        return None

    if current_phase not in definition.phases:
        # current_phase が定義に含まれていないが、
        # もし定義の最後が終わった後なら result へ
        # しかし通常は phase リスト外の挙動は未定義
        # ここでは安全のため "result" を返すかエラーにするかだが、
        # "result" は特殊フェーズとして扱う
        return None

    try:
        idx = definition.phases.index(current_phase)
        if idx + 1 < len(definition.phases):
            return definition.phases[idx + 1]
        else:
            # 定義されたフェーズの最後 -> result
            return "result"
    except ValueError:
        return None
