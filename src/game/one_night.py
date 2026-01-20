from src.core.types import RoleName, GameDefinition, RoleDefinition


ROLE_LLM_DESCRIPTIONS: dict[RoleName, str] = {
    "villager": (
        "You are a villager in a one-night werewolf game. "
        "You have no special abilities and receive no private information. "
        "During discussion, carefully analyze others' statements and inconsistencies. "
        "Your goal is to identify werewolves and vote for them, based only on logic and behavior."
    ),
    "werewolf": (
        "You are a werewolf in a one-night werewolf game. "
        "You know that you are a werewolf, but others do not. "
        "During discussion, you must deceive villagers, avoid suspicion, "
        "and manipulate the conversation so that villagers vote incorrectly."
    ),
    "seer": (
        "You are a seer in a one-night werewolf game. "
        "During the night, you inspected one player and learned their role. "
        "During discussion, decide carefully whether to reveal this information, "
        "partially hint at it, or keep it secret, in order to help villagers identify werewolves."
    ),
    "madman": (
        "You are a madman in a one-night werewolf game. "
        "You appear as a villager if inspected, but you win only if the werewolves win. "
        "During discussion, subtly support the werewolves without revealing your true role, "
        "and try to mislead villagers while appearing helpful."
    ),
}

# =========================
# ワンナイト人狼のゲーム定義（固定）
# =========================

ONE_NIGHT_GAME_DEFINITION = GameDefinition(
    roles={
        "villager": RoleDefinition(
            name="villager",
            day_side="village",
            win_side="village",
            ability_type="none",
        ),
        "seer": RoleDefinition(
            name="seer",
            day_side="village",
            win_side="village",
            ability_type="seer",
        ),
        "werewolf": RoleDefinition(
            name="werewolf",
            day_side="werewolf",
            win_side="werewolf",
            ability_type="werewolf",
        ),
        "madman": RoleDefinition(
            name="madman",
            day_side="village",  # 昼は村人扱い
            win_side="werewolf",  # 勝利条件は人狼側
            ability_type="none",
            divine_result_as_role="villager",
        ),
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
