from core.types import GameDefinition

GAME_DEF: GameDefinition = {
    "roles": {
        "villager": {
            "name": "villager",
            "description": "An ordinary villager with no special ability.",
            "team": "village",
        },
        "werewolf": {
            "name": "werewolf",
            "description": "A werewolf who tries to avoid being discovered.",
            "team": "werewolf",
        },
        "seer": {
            "name": "seer",
            "description": "Can inspect one player during the night to learn their role.",
            "team": "village",
        },
    },
    "role_distribution": [
        "villager",
        "villager",
        "werewolf",
        "seer",
        "werewolf",
    ],
    "win_conditions": {
        "village": "At least one werewolf is eliminated during the vote.",
        "werewolf": "No werewolf is eliminated during the vote.",
    },
    "player_count": 5,
    "phases": ["night", "day", "vote"],
    "rules": [
        "The game consists of a single night, a single day discussion, and one vote.",
        "After the vote, the game ends immediately.",
        "There is no second night phase.",
        "Each role ability can be used at most once during the night.",
        "Only the voting result determines the winner.",
    ],
}
