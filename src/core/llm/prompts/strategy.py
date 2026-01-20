from .base import ONE_NIGHT_WEREWOLF_RULES
from .roles import get_role_strategy_section

# =============================================================================
# STRATEGY GENERATION PROMPTS
# =============================================================================

COMMON_STRATEGY_OUTPUT_FORMAT = """
{
  "co_decision": "co_now" | "co_later" | "no_co" | null,
  "co_target": "player name or null",
  "co_result": "人狼" | "村人" | null,
  "target_player": "player name or null",
  "value_focus": "logic" | "emotion" | "trust" | "aggression",
  "aggression_level": 1-10 (integer),
  "doubt_level": 1-10 (integer),
  "action_type": "co" | "agree" | "disagree" | "question" | "vote_inducement" | "skip",
  "style_instruction": "Short style guideline"
}
"""


# =============================================================================
# DYNAMIC STRATEGY PROMPT GENERATOR
# =============================================================================

def get_strategy_system_prompt(role: str) -> str:
    """
    指定された役職に対応する戦略生成用システムプロンプトを返す。
    
    Args:
        role: 役職名 (villager, seer, werewolf, madman)
    
    Returns:
        役職固有の戦略システムプロンプト
    """
    role_strategy = get_role_strategy_section(role)
    
    return f"""\
{ONE_NIGHT_WEREWOLF_RULES}

{role_strategy}
## OUTPUT FORMAT (JSON ONLY)
{COMMON_STRATEGY_OUTPUT_FORMAT}
"""


# =============================================================================
# LEGACY ROLE-SPECIFIC PROMPTS (Deprecated - Use get_strategy_system_prompt)
# =============================================================================
# 下位互換性のため維持。新規コードは get_strategy_system_prompt() を使用すること。

SEER_STRATEGY_SYSTEM_PROMPT = get_strategy_system_prompt("seer")
WEREWOLF_STRATEGY_SYSTEM_PROMPT = get_strategy_system_prompt("werewolf")
MADMAN_STRATEGY_SYSTEM_PROMPT = get_strategy_system_prompt("madman")
VILLAGER_STRATEGY_SYSTEM_PROMPT = get_strategy_system_prompt("villager")


# =============================================================================
# REVIEW & REFINE
# =============================================================================

STRATEGY_REVIEW_SYSTEM_PROMPT = f"""\
Review the player's strategy.
{ONE_NIGHT_WEREWOLF_RULES}

## CHECKLIST
1. Is the strategy consistent with the role?
2. Are `co_target` and `co_result` set if `co_decision` is "co_now"?
3. If ALREADY CO'd: Ensure `action_type` is NOT "co" again. Instead, use "agree", "disagree", or "vote_inducement".

## OUTPUT FORMAT (JSON)
{{
  "needs_fix": boolean,
  "reason": "short explanation",
  "fix_instruction": "single sentence (null if no fix needed)"
}}
"""

STRATEGY_REFINE_SYSTEM_PROMPT = f"""\
Refine the strategy JSON based on the review.
{ONE_NIGHT_WEREWOLF_RULES}

Input: original_strategy, review_reason, fix_instruction
Output: Corrected JSON using common format.
{COMMON_STRATEGY_OUTPUT_FORMAT}
"""

