from .base import ONE_NIGHT_WEREWOLF_RULES
from .roles import get_role_interaction_summary

INITIAL_STRATEGY_OUTPUT_FORMAT = """
{{
  "initial_goal": "The ultimate victory condition in this game",
  "victory_condition": "Specific state required to win",
  "defeat_condition": "State that leads to defeat",
  "role_behavior": "Behavioral policy for the role",
  "must_not_do": [
    "List of actions to strictly avoid"
  ],
  "recommended_actions": [
    "List of recommended actions to achieve the goal"
  ],
  "co_policy": "immediate" | "wait_and_see" | "counter_co",
  "intended_co_role": "seer" | "villager" | "werewolf" | "madman" | null
}}
"""

# =============================================================================
# INITIAL STRATEGY SYSTEM PROMPT
# =============================================================================
#
# 設計原則:
# - System Prompt: 戦略計画の目的と出力フォーマット
# - Runtime Prompt で提供すべきもの:
#   - 役職固有のコンテキスト
#   - ゲーム定義（Role Distribution）
# =============================================================================

INITIAL_STRATEGY_SYSTEM_PROMPT = f"""\
You are a player in ONE-NIGHT Werewolf (Night Phase).
{ONE_NIGHT_WEREWOLF_RULES}

## OBJECTIVE
Decide your long-term **strategic plan** for this game.
This plan will guide your actions throughout the discussion.

## PLANNING FRAMEWORK
Define the following:
1. **Victory Condition**: How do you win?
2. **Defeat Condition**: What causes you to lose?
3. **Actions to Avoid**: What will ruin your game?
4. **Recommended Actions**: What will help you succeed?

## OUTPUT FORMAT (JSON ONLY)
{INITIAL_STRATEGY_OUTPUT_FORMAT}
"""

