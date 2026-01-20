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
        
        print("[BeliefGenerator] Building prompts completed")
        print(f"[BeliefGenerator] System prompt length: {len(system)}")
        print(f"[BeliefGenerator] User prompt length: {len(user)}")

        try:
            print("[BeliefGenerator] Calling LLM.generate()...")
            result: RoleBeliefsOutput = self.llm.generate(
                system=system,
                prompt=user,
            )
            print("[BeliefGenerator] LLM.generate() returned")

            beliefs: Dict[PlayerName, RoleProb] = {}

            for item in result.beliefs:
                # RoleProbOutput -> RoleProb convert
                # 動的に全役職の確率を抽出
                from src.core.roles import get_all_role_names
                
                probs = {}
                for role_name in get_all_role_names():
                    # Pydanticモデルのフィールドから動的に取得を試みる
                    # getattr(item.belief, role_name, 0.0)
                    # NOTE: item.belief は RoleProbOutput (Pydantic) なので、
                    # 固定フィールドしか持っていない場合は、動的役職に対応するために
                    # RoleProbOutput 自体の定義変更も必要になる可能性がある。
                    # 現状は RoleProbOutput が Dict[str, float] または全役職フィールドを持つと仮定
                    
                    val = getattr(item.belief, role_name, None)
                    if val is None:
                        # item.belief が辞書型のように振る舞う場合、あるいは extra fields
                        val = 0.0
                    probs[role_name] = val
                
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
        from src.core.roles import get_all_role_names

        observed_type = observed.__class__.__name__

        current_beliefs = "\n".join(
            f"- {player}: {belief.probs}"
            for player, belief in memory.role_beliefs.items()
        )

        # 全役職のリストを動的に生成
        all_roles = get_all_role_names()
        role_fields = "\n        ".join(f'"{role}": 0.X,' for role in all_roles)

        system = f"""
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
{{
  "beliefs": [
    {{
      "player": "Alice",
      "belief": {{
        {role_fields}
      }}
    }},
    {{
      "player": "Bob",
      "belief": {{ ... }}
    }}
  ]
}}
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
