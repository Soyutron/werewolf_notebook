from .base import ONE_NIGHT_WEREWOLF_RULES
from .common import REFLECTION_SYSTEM_PROMPT, REACTION_SYSTEM_PROMPT
from .gm import (
    GM_COMMENT_SYSTEM_PROMPT,
    GM_MATURITY_SYSTEM_PROMPT,
    GM_COMMENT_REVIEW_SYSTEM_PROMPT,
    GM_COMMENT_REFINE_SYSTEM_PROMPT,
)
from .player import (
    SPEAK_SYSTEM_PROMPT,
    SPEAK_REVIEW_SYSTEM_PROMPT,
    SPEAK_REFINE_SYSTEM_PROMPT,
)
from .strategy import (
    get_strategy_system_prompt,
    SEER_STRATEGY_SYSTEM_PROMPT,
    WEREWOLF_STRATEGY_SYSTEM_PROMPT,
    MADMAN_STRATEGY_SYSTEM_PROMPT,
    VILLAGER_STRATEGY_SYSTEM_PROMPT,
    STRATEGY_REVIEW_SYSTEM_PROMPT,
    STRATEGY_REFINE_SYSTEM_PROMPT,
)
from .strategy_plan import INITIAL_STRATEGY_SYSTEM_PROMPT
from .roles import (
    get_role_name_ja,
    get_role_description,
    get_role_goal,
    get_role_interaction_summary,
    # Backward compatibility aliases
    get_role_strategy_section,
    get_role_requirements,
    get_role_interaction_hints,
)

__all__ = [
    "ONE_NIGHT_WEREWOLF_RULES",
    "REFLECTION_SYSTEM_PROMPT",
    "REACTION_SYSTEM_PROMPT",
    "GM_COMMENT_SYSTEM_PROMPT",
    "GM_MATURITY_SYSTEM_PROMPT",
    "GM_COMMENT_REVIEW_SYSTEM_PROMPT",
    "GM_COMMENT_REFINE_SYSTEM_PROMPT",
    "SPEAK_SYSTEM_PROMPT",
    "SPEAK_REVIEW_SYSTEM_PROMPT",
    "SPEAK_REFINE_SYSTEM_PROMPT",
    "get_strategy_system_prompt",
    "SEER_STRATEGY_SYSTEM_PROMPT",
    "WEREWOLF_STRATEGY_SYSTEM_PROMPT",
    "MADMAN_STRATEGY_SYSTEM_PROMPT",
    "VILLAGER_STRATEGY_SYSTEM_PROMPT",
    "STRATEGY_REVIEW_SYSTEM_PROMPT",
    "STRATEGY_REFINE_SYSTEM_PROMPT",
    "INITIAL_STRATEGY_SYSTEM_PROMPT",
    "INITIAL_STRATEGY_SYSTEM_PROMPT",
    "get_role_name_ja",
    "get_role_description",
    "get_role_goal",
    "get_role_interaction_summary",
    # Backward compatibility
    "get_role_strategy_section",
    "get_role_requirements",
    "get_role_interaction_hints",
]

