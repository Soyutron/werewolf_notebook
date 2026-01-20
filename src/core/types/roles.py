"""
役職・陣営関連の型定義

責務:
- 役職名の定義
- 陣営（昼の立場/勝利条件）の定義
- 役職の構造定義
"""

from typing import Literal
from pydantic import BaseModel

__all__ = [
    "RoleName",
    "Side",
    "DaySide",
    "WinSide",
    "RoleDefinition",
]


# =========================
# 役職名・陣営名を Literal で固定
# =========================

# =========================
# 役職名・陣営名の Literal で固定（後方互換性のため維持）
# =========================
# NOTE: 将来的には Literal 指定を廃止し、str ベースで運用する
RoleName = str

# =========================
# 陣営（Side）の定義
# =========================
# ゲームにおける「陣営」を表す共通カテゴリ
# ・昼フェーズでの立場（DaySide）
# ・最終的な勝利条件の帰属（WinSide）
# の両方で使用される
Side = str
# 元の定義（参考）: Literal["village", "werewolf"]

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
class RoleDefinition(BaseModel):
    name: RoleName  # 役職名（例: "villager", "werewolf"）
    day_side: DaySide  # 昼の立場
    win_side: WinSide  # 勝利条件の帰属
    ability_type: str = "none"  # 能力の種類
    divine_result_as_role: RoleName | None = None  # 占われた時の見え方（Noneの場合はnameと同じ）
    # NOTE:
    # - day_side は「昼フェーズでの扱い」を表す
    # - win_side は「最終勝敗判定のみ」に使用される
    # - 両者は一致するとは限らない（例: madman）
