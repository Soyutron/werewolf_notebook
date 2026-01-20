# src/core/llm/prompts/roles.py
"""
役職定義の一元管理モジュール

責務:
- 全役職の名前・説明・戦略・要件を一箇所で定義
- 各種プロンプトから参照される Single Source of Truth
- 役職固有の情報を動的に取得するヘルパー関数を提供
"""

from typing import Dict, Any
from pydantic import BaseModel

__all__ = [
    "ROLE_NAMES",
    "ROLE_DEFINITIONS",
    "get_role_name_ja",
    "get_role_strategy_section",
    "get_role_requirements",
    "get_role_interaction_hints",
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
    """役職の詳細定義"""
    description: str  # 役職の説明
    goal: str  # 勝利目標
    ability: str  # 特殊能力（なければ空文字）
    day_side: str  # 昼フェーズでの扱い
    win_side: str  # 勝利条件の帰属
    strategy_hints: str  # 戦略のヒント
    requirements: str  # プレイヤーへの要件


ROLE_DEFINITIONS: Dict[str, RoleDefinitionData] = {
    "villager": RoleDefinitionData(
        description="特殊能力を持たない基本役職。議論と推理のみで人狼を見つける。",
        goal="人狼を処刑する",
        ability="",
        day_side="village",
        win_side="village",
        strategy_hints="""
- **Goal**: Find the Werewolf.
- **Parameters**:
  - `aggression_level`: Moderate. Rise if someone is clearly lying.
  - `value_focus`: "logic" (deduction).
- **Actions**:
  - `agree` / `disagree`: Validate claims.
  - `question`: Clarify suspicion.
  - `vote_inducement`: When confident.""",
        requirements="MUST be active. Silence or neutrality is unacceptable.",
    ),
    "seer": RoleDefinitionData(
        description="夜フェーズに一人のプレイヤーの役職を占うことができる。",
        goal="人狼を処刑する",
        ability="夜に1人の役職を確認できる",
        day_side="village",
        win_side="village",
        strategy_hints="""
- **Truth**: You know the true role of one player.
- **Goal**: Persuade the village to trust your result.
- **Parameters**:
  - `aggression_level`: High when attacking liars.
  - `value_focus`: "logic" (contradictions) or "trust" (appearing stable).
- **Actions**:
  - `co`: Reveal your result immediately (High Priority).
  - `vote_inducement`: Lead the vote against liars.""",
        requirements="MUST CO with specific result (Target + White/Black). Omitting result is FORBIDDEN.",
    ),
    "werewolf": RoleDefinitionData(
        description="村を欺く敵陣営。処刑されないように振る舞う。",
        goal="処刑を回避して生き残る",
        ability="",
        day_side="village",  # 昼は村人として扱われる（隠れている）
        win_side="werewolf",
        strategy_hints="""
- **Goal**: SURVIVE.
- **Parameters**:
  - `aggression_level`: Variable. Too high = suspicious, too low = weak.
  - `doubt_level`: Fake suspicion to fit in.
- **Actions**:
  - `co` (FAKE): Claim Seer/Villager to misdirect.
  - `agree`: Support potential allies (Madman).
  - `question`: Deflect suspicion.""",
        requirements="MUST survive (fake CO allowed). Avoid vagueness.",
    ),
    "madman": RoleDefinitionData(
        description="人狼陣営の味方。占い判定は「村人」だが、勝利条件は人狼側。",
        goal="人狼の勝利に貢献する",
        ability="",
        day_side="village",  # 占いで村人と判定される
        win_side="werewolf",
        strategy_hints="""
- **Goal**: Help the Werewolf win.
- **Parameters**:
  - `aggression_level`: Can be erratic or high to disrupt.
  - `value_focus`: "emotion" or "aggression" to create chaos.
- **Actions**:
  - `co` (FAKE): Counter-claim Seer (High Priority).
  - `disagree`: Create conflict.
  - `vote_inducement`: Push for bad execution.""",
        requirements="MUST mislead the village. Tone: calm, factual.",
    ),
}


# =============================================================================
# ヘルパー関数: プロンプト構築用
# =============================================================================

def get_role_strategy_section(role: str) -> str:
    """
    指定された役職の戦略セクションを返す。
    strategy.py の役職別プロンプトで使用。
    """
    role_def = ROLE_DEFINITIONS.get(role)
    if not role_def:
        return ""
    
    role_name_ja = get_role_name_ja(role)
    role_name_en = ROLE_NAMES.get(role, {}).get("en", role)
    
    return f"""## ROLE STRATEGY
You are {role_name_ja} ({role_name_en}).
{role_def.strategy_hints}
"""


def get_role_requirements() -> str:
    """
    全役職の要件を返す。
    player.py の _ROLE_REQUIREMENTS で使用。
    """
    lines = ["ROLE REQUIREMENTS:"]
    for role, role_def in ROLE_DEFINITIONS.items():
        role_name_ja = get_role_name_ja(role)
        role_name_en = ROLE_NAMES.get(role, {}).get("en", role)
        lines.append(f"- {role_name_ja} ({role_name_en}): {role_def.requirements}")
    return "\n".join(lines)


def get_role_interaction_hints() -> str:
    """
    役職間の相互作用ヒントを返す。
    strategy_plan.py の ROLE_INTERACTION_HINTS で使用。
    """
    lines = ["## ROLE INTERACTIONS & HINTS", "Consider how other roles might act:"]
    
    hints = {
        "seer": "Can see 1 player. High info, high credibility target.",
        "werewolf": "Must deceive other players to avoid being identified. Wins if the Werewolf team wins.",
        "madman": 'Wins if Werewolf wins. Zero info. If investigated by the Seer, the result is always "Villager." Needs to confuse/act as bait/protect Werewolf.',
        "villager": "No info. Needs to deduce from others' claims and inconsistencies.",
    }
    
    for role, hint in hints.items():
        role_name_ja = get_role_name_ja(role)
        role_name_en = ROLE_NAMES.get(role, {}).get("en", role)
        lines.append(f"- **{role_name_en}**: {hint}")
    
    return "\n".join(lines)
