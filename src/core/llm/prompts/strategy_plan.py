from .base import ONE_NIGHT_WEREWOLF_RULES
from .roles import get_role_interaction_hints

INITIAL_STRATEGY_OUTPUT_FORMAT = """
{{
  "initial_goal": "The ultimate victory condition or goal in this game (e.g., 'Win trust as Seer', 'Avoid execution as Werewolf')",
  "victory_condition": "Specific state or condition required to win (e.g., 'Ensure I survive when a Werewolf is executed')",
  "defeat_condition": "State or condition that leads to defeat (e.g., 'Being executed on Day 1', 'Being suspected as a Werewolf')",
  "role_behavior": "Behavioral policy for the role (e.g., 'Lurk and gather info', 'Aggressively CO to disrupt')",
  "must_not_do": [
    "List of actions or situations to strictly avoid (e.g., 'Contradicting myself', 'staying too silent')"
  ],
  "recommended_actions": [
    "List of recommended actions to achieve the strategic goal (e.g., 'Ask probing questions', 'Guide votes toward suspicious players')"
  ],
  "co_policy": "immediate" | "wait_and_see" | "counter_co",
  "intended_co_role": "seer" | "villager" | "werewolf" | "madman" | null
}}
"""

# 役職間相互作用ヒント（roles.py から取得）
ROLE_INTERACTION_HINTS = get_role_interaction_hints()

INITIAL_STRATEGY_SYSTEM_PROMPT = f"""\
You are a player in ONE-NIGHT Werewolf (Night Phase).
{ONE_NIGHT_WEREWOLF_RULES}

## ROLE
You are: {{role}}

{ROLE_INTERACTION_HINTS}

## OBJECTIVE
Decide your long-term **strategic plan**.
This plan will guide your actions throughout the game.

You must clearly define:
1. **Victory Condition**: How exactly do you win?
2. **Defeat Condition**: What specific scenarios cause you to lose?
3. **MUST NOT DO**: What actions will ruin your game? (e.g. "Contradicting my own CO", "Voting for a confirmed human")
4. **RECOMMENDED ACTIONS**: What actions will help you achieve your goal? (e.g. "Ask probing questions", "Build trust by agreeing with logical points")

Select a CO policy consistent with your role (e.g., Seer usually "immediate", Villager "no_co").

## OUTPUT FORMAT (JSON ONLY)
{INITIAL_STRATEGY_OUTPUT_FORMAT}
"""
