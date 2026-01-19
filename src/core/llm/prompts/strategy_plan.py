from .base import ONE_NIGHT_WEREWOLF_RULES

INITIAL_STRATEGY_OUTPUT_FORMAT = """
{{
  "initial_goal": "The ultimate victory condition or goal in this game (e.g., 'Win trust as Seer', 'Avoid execution as Werewolf')",
  "victory_condition": "Specific state or condition required to win (e.g., 'Ensure I survive when a Werewolf is executed')",
  "defeat_condition": "State or condition that leads to defeat (e.g., 'Being executed on Day 1', 'Being suspected as a Werewolf')",
  "role_behavior": "Behavioral policy for the role (e.g., 'Lurk and gather info', 'Aggressively CO to disrupt')",
  "must_not_do": [
    "List of actions or situations to strictly avoid (e.g., 'Contradicting myself', 'staying too silent')"
  ],
  "co_policy": "immediate" | "wait_and_see" | "counter_co",
  "intended_co_role": "seer" | "villager" | "werewolf" | "madman" | null
}}
"""

ROLE_INTERACTION_HINTS = """
## ROLE INTERACTIONS & HINTS
Consider how other roles might act:
- **Seer**: Can see 1 player. High info, high credibility target.
- **Werewolf**: Must deceive other players to avoid being identified. Wins if the Werewolf team wins.
- **Madman**: Wins if Werewolf wins. Zero info. If investigated by the Seer, the result is always “Villager.” Needs to confuse/act as bait/protect Werewolf.
- **Villager**: No info. Needs to deduce from others' claims and inconsistencies.
"""

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

Select a CO policy consistent with your role (e.g., Seer usually "immediate", Villager "no_co").

## OUTPUT FORMAT (JSON ONLY)
{INITIAL_STRATEGY_OUTPUT_FORMAT}
"""
