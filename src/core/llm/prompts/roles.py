# src/core/llm/prompts/roles.py
"""
役職定義の一元管理モジュール

責務:
- 全役職の名前・説明・勝利条件を一箇所で定義
- 各種プロンプトから参照される Single Source of Truth
- 役職固有の情報を動的に取得するヘルパー関数を提供

設計原則:
- 役職の本質的特性のみを定義
- 具体的な行動リストやパラメータ値は含まない
- 状況依存の戦術は runtime prompt で提供
"""

from typing import Dict, Any
from pydantic import BaseModel

__all__ = [
    "ROLE_NAMES",
    "ROLE_DEFINITIONS",
    "get_role_name_ja",
    "get_role_description",
    "get_role_goal",
    "get_role_interaction_summary",
]


# =============================================================================
# 役職名マッピング
# =============================================================================

ROLE_NAMES: Dict[str, Dict[str, str]] = {
    "villager": {"ja": "村人", "en": "Villager"},
    "seer": {"ja": "占い師", "en": "Seer"},
    "werewolf": {"ja": "人狼", "en": "Werewolf"},
    "madman": {"ja": "狂人", "en": "Madman"},
}


def get_role_name_ja(role: str) -> str:
    """役職の日本語名を取得する"""
    return ROLE_NAMES.get(role, {}).get("ja", role)


# =============================================================================
# 役職定義データ
# =============================================================================

class RoleDefinitionData(BaseModel):
    """役職の詳細定義（本質的特性のみ）"""
    description: str  # 役職の説明
    goal: str  # 勝利目標
    ability: str  # 特殊能力（なければ空文字）
    win_side: str  # 勝利条件の帰属 (village / werewolf)
    core_principle: str  # 役職の本質的な行動原則（1文）


ROLE_DEFINITIONS: Dict[str, RoleDefinitionData] = {
    "villager": RoleDefinitionData(
        description="特殊能力を持たない基本役職。議論と推理のみで人狼を見つける。",
        goal="人狼を処刑する",
        ability="",
        win_side="village",
        core_principle="論理的な推論で人狼を見つけ出し、他者を説得する。",
    ),
    "seer": RoleDefinitionData(
        description="夜フェーズに一人のプレイヤーの役職を占うことができる。",
        goal="人狼を処刑する",
        ability="夜に1人の役職を確認できる",
        win_side="village",
        core_principle="確定情報を活用して、村を正しい投票へと導く。",
    ),
    "werewolf": RoleDefinitionData(
        description="村を欺く敵陣営。処刑されないように振る舞う。",
        goal="処刑を回避して生き残る",
        ability="",
        win_side="werewolf",
        core_principle="村人を欺き、投票による追放を回避する。",
    ),
    "madman": RoleDefinitionData(
        description="人狼陣営の味方。占い判定は「村人」だが、勝利条件は人狼側。",
        goal="人狼の勝利に貢献する",
        ability="",
        win_side="werewolf",
        core_principle="誰が人狼か知らぬまま、混乱を招いて人狼を守る。",
    ),
}


# =============================================================================
# ヘルパー関数: プロンプト構築用
# =============================================================================

def get_role_description(role: str) -> str:
    """
    指定された役職の基本説明を返す。
    """
    role_def = ROLE_DEFINITIONS.get(role)
    if not role_def:
        return ""
    
    role_name_ja = get_role_name_ja(role)
    role_name_en = ROLE_NAMES.get(role, {}).get("en", role)
    
    parts = [f"あなたは{role_name_ja}（{role_name_en}）です。"]
    parts.append(f"目標: {role_def.goal}")
    if role_def.ability:
        parts.append(f"能力: {role_def.ability}")
    parts.append(f"行動原則: {role_def.core_principle}")
    
    return "\n".join(parts)


def get_role_goal(role: str) -> str:
    """役職の勝利目標を返す"""
    role_def = ROLE_DEFINITIONS.get(role)
    return role_def.goal if role_def else ""


def get_role_interaction_summary() -> str:
    """
    役職間の相互作用サマリーを返す。
    抽象的なレベルでの役職特性のみ。
    """
    lines = ["## 役職概要"]
    
    for role, role_def in ROLE_DEFINITIONS.items():
        role_name_ja = get_role_name_ja(role)
        lines.append(f"- **{role_name_ja}** ({role_def.win_side}陣営): {role_def.core_principle}")
    
    return "\n".join(lines)


# =============================================================================
# 後方互換性のためのエイリアス（非推奨）
# =============================================================================

def get_role_strategy_section(role: str) -> str:
    """
    後方互換性のため維持。get_role_description() を使用してください。
    """
    return f"## ROLE\n{get_role_description(role)}"


def get_role_requirements() -> str:
    """
    後方互換性のため維持。
    具体的な要件は runtime prompt で提供すべき。
    """
    lines = ["ROLE OVERVIEW:"]
    for role, role_def in ROLE_DEFINITIONS.items():
        role_name_ja = get_role_name_ja(role)
        lines.append(f"- {role_name_ja}: {role_def.core_principle}")
    return "\n".join(lines)


def get_role_interaction_hints() -> str:
    """
    後方互換性のため維持。get_role_interaction_summary() を使用してください。
    """
    return get_role_interaction_summary()

