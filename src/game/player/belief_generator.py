from typing import Optional, Dict, Union

from src.core.llm.client import LLMClient
from src.core.memory.belief import RoleBeliefsOutput
from src.core.types import (
    PlayerMemory,
    GameEvent,
    PlayerRequest,
    PlayerName,
    RoleProb,
)
from src.config.llm import create_belief_llm


Observed = Union[GameEvent, PlayerRequest]


class BeliefGenerator:
    """
    PlayerMemory と新しく観測したイベントから
    role_beliefs（確率分布）を生成するクラス。

    設計方針:
    - belief は主観・不確実な推論
    - 更新ロジックは LLM に委譲する
    - state は直接変更しない
    - LLM が失敗した場合は None を返す
    """

    def __init__(self, llm: LLMClient[RoleBeliefsOutput]):
        self.llm = llm

    def generate(
        self,
        *,
        memory: PlayerMemory,
        observed: Observed,
    ) -> Optional[Dict[PlayerName, RoleProb]]:
        """
        role_beliefs を丸ごと生成する。

        失敗した場合は None を返す。
        """
        system, user = self._build_prompts(memory, observed)

        try:
            result: RoleBeliefsOutput = self.llm.generate(
                system=system,
                prompt=user,
            )

            beliefs: Dict[PlayerName, RoleProb] = {}

            for item in result.beliefs:
                # RoleProbOutput -> RoleProb convert
                probs = {
                    "villager": item.belief.villager,
                    "seer": item.belief.seer,
                    "werewolf": item.belief.werewolf,
                    "madman": item.belief.madman,
                }
                
                # Normalize manually since RoleProb.normalize doesn't exist
                total = sum(probs.values())
                if total > 0:
                    probs = {k: v / total for k, v in probs.items()}
                else:
                    # Fallback uniform distribution
                    probs = {k: 0.25 for k in probs}

                beliefs[item.player] = RoleProb(probs=probs)

            return beliefs

        except Exception as e:
            import traceback
            traceback.print_exc()
            # 推論に失敗してもゲーム進行は止めない
            return None

    def _build_prompts(
        self,
        memory: PlayerMemory,
        observed: Observed,
    ) -> tuple[str, str]:
        """
        system / user prompt を構築する。
        """
        observed_type = observed.__class__.__name__

        current_beliefs = "\n".join(
            f"- {player}: {belief.probs}"
            for player, belief in memory.role_beliefs.items()
        )

        system = """
You are an AI player in a Werewolf-style social deduction game.
You must update your private beliefs about each player's role based on a new observation.

Rules:
- Output ONLY updated role beliefs.
- Beliefs must be probabilistic (no certainty).
- Do NOT use 0.0 or 1.0 probabilities.
- Probabilities for each player must sum to exactly 1.0.
- Do NOT change your own role.
- Do NOT explain your reasoning.
- Output JSON list of objects.

Output format:
{
  "beliefs": [
    {
      "player": "Alice",
      "belief": {
        "villager": 0.4,
        "seer": 0.3,
        "werewolf": 0.3,
        "madman": 0.0
      }
    },
    {
      "player": "Bob",
      "belief": { ... }
    }
  ]
}
"""
        user = f"""
Current players:
{memory.players}

Your own name:
{memory.self_name}

Your own role (this is fixed and must not change):
{memory.self_role}

Current role beliefs (private):
{current_beliefs}

New observation:
Type: {observed_type}
Details:
{observed.model_dump()}
"""
        return system.strip(), user.strip()


# --- グローバルに1つだけ ---
believe_generator = BeliefGenerator(llm=create_belief_llm())
