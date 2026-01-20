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
    "get_role_name_ja",
    "get_role_description",
    "get_role_goal",
    "get_role_interaction_summary",
]


# =============================================================================
# 役職名マッピング
# =============================================================================

# =============================================================================
# 役職定義データへのアクセス
# =============================================================================

from src.core.roles import (
    role_registry,
    get_role_display_name,
    get_role_config,
    get_role_advice,
    get_all_role_names,
)


def get_role_name_ja(role: str) -> str:
    """役職の日本語名を取得する"""
    return get_role_display_name(role, "ja")


# =============================================================================
# ヘルパー関数: プロンプト構築用
# =============================================================================

def get_role_description(role: str) -> str:
    """
    指定された役職の基本説明を返す。
    """
    role_def = get_role_config(role)
    if not role_def:
        return ""
    
    role_name_ja = get_role_display_name(role, "ja")
    role_name_en = get_role_display_name(role, "en")
    
    parts = [f"あなたは{role_name_ja}（{role_name_en}）です。"]
    parts.append(f"目標: {role_def.goal}")
    if role_def.ability:
        parts.append(f"能力: {role_def.ability}")
    parts.append(f"行動原則: {role_def.core_principle}")
    
    return "\n".join(parts)


def get_role_goal(role: str) -> str:
    """役職の勝利目標を返す"""
    role_def = get_role_config(role)
    return role_def.goal if role_def else ""


def get_role_interaction_summary() -> str:
    """
    役職間の相互作用サマリーを返す。
    抽象的なレベルでの役職特性のみ。
    """
    lines = ["## 役職概要"]
    
    for role in get_all_role_names():
        role_def = get_role_config(role)
        if not role_def:
            continue
        role_name_ja = get_role_display_name(role, "ja")
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
    for role in get_all_role_names():
        role_def = get_role_config(role)
        role_name_ja = get_role_display_name(role, "ja")
        lines.append(f"- {role_name_ja}: {role_def.core_principle}")
    return "\n".join(lines)


def get_role_interaction_hints() -> str:
    """
    後方互換性のため維持。get_role_interaction_summary() を使用してください。
    """
    return get_role_interaction_summary()

