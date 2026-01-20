from src.core.types import RoleName, GameDefinition, RoleDefinition
from src.core.roles import role_registry
from src.core.llm.prompts.roles import get_role_description



ROLE_LLM_DESCRIPTIONS: dict[RoleName, str] = {
    name: get_role_description(name)
    for name in role_registry.get_all_names()
}

# =========================
# ワンナイト人狼のゲーム定義（固定）
# =========================

ONE_NIGHT_GAME_DEFINITION = GameDefinition(
    roles={
        name: RoleDefinition(
            name=name,
            day_side=config.day_side,
            win_side=config.win_side,
            ability_type=config.ability_type,
            divine_result_as_role=config.divine_result_as_role,
        )
        for name, config in role_registry.get_all().items()
    },
    role_distribution=[
        "villager",
        "villager",
        "seer",
        "werewolf",
        "madman",
    ],
    phases=[
        "night",
        "day",
        "vote",
    ],
)
