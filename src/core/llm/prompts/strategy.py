from .base import ONE_NIGHT_WEREWOLF_RULES
from .roles import get_role_description

# =============================================================================
# STRATEGY GENERATION PROMPTS
# =============================================================================
#
# 設計原則:
# - System Prompt: 戦略生成の目的と出力フォーマット
# - Runtime Prompt で提供すべきもの:
#   - 現在のゲーム状況
#   - 他プレイヤーの発言履歴
#   - Belief 情報
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
    role_description = get_role_description(role)
    
    return f"""\
You are generating an ACTION GUIDELINE for ONE-NIGHT Werewolf.
{ONE_NIGHT_WEREWOLF_RULES}

## ROLE
{role_description}

## DESIGN PRINCIPLE
Your Strategic Plan (provided in the prompt) is the SOURCE OF TRUTH.
- The StrategyPlan was decided at game start and defines your overall approach
- Your task is to generate tactical parameters for THIS TURN that EXECUTE the plan
- Do NOT reinterpret, override, or contradict the StrategyPlan
- Adapt to the CURRENT SITUATION while staying consistent with the plan

## OBJECTIVE
Generate action parameters that:
1. Execute your StrategyPlan's goals and policies
2. Adapt to the immediate game situation
3. Avoid all actions listed in "MUST NOT DO"
4. Prioritize actions listed in "RECOMMENDED ACTIONS"

## OUTPUT FORMAT (JSON ONLY)
{COMMON_STRATEGY_OUTPUT_FORMAT}
"""


# =============================================================================
# LEGACY ROLE-SPECIFIC PROMPTS (Deprecated - Use get_strategy_system_prompt)
# =============================================================================

SEER_STRATEGY_SYSTEM_PROMPT = get_strategy_system_prompt("seer")
WEREWOLF_STRATEGY_SYSTEM_PROMPT = get_strategy_system_prompt("werewolf")
MADMAN_STRATEGY_SYSTEM_PROMPT = get_strategy_system_prompt("madman")
VILLAGER_STRATEGY_SYSTEM_PROMPT = get_strategy_system_prompt("villager")


# =============================================================================
# REVIEW & REFINE
# =============================================================================
#
# 設計原則:
# - Review: ルール違反や論理矛盾のみチェック
# - Refine: 指摘された問題のみ修正
# =============================================================================

STRATEGY_REVIEW_SYSTEM_PROMPT = f"""\
Review the player's strategy for consistency with their role.
{ONE_NIGHT_WEREWOLF_RULES}

## CHECKLIST
1. Is the strategy consistent with the role's win condition?
2. Are required fields properly set (e.g., co_target/co_result for co_now)?
3. Does the action_type make sense given the game state?

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

## INSTRUCTIONS
- Fix only the issue specified in fix_instruction.
- Preserve the overall intent of the strategy.

## OUTPUT FORMAT
{COMMON_STRATEGY_OUTPUT_FORMAT}
"""

