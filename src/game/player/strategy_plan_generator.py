from typing import Optional
from src.core.llm.client import LLMClient
from src.core.llm.prompts import INITIAL_STRATEGY_SYSTEM_PROMPT
from src.core.memory.strategy import StrategyPlan
from src.core.types.player import PlayerMemory

class StrategyPlanGenerator:
    """
    [Night Phase] プレイヤーの初期戦略計画(StrategyPlan)を生成するクラス。
    """

    def __init__(self, llm: LLMClient):
        self.llm = llm

    def generate(self, memory: PlayerMemory) -> Optional[StrategyPlan]:
        """
        ゲーム開始時点の初期戦略計画を生成する。
        """
        try:
            prompt = self._build_prompt(memory)
            plan: StrategyPlan = self.llm.generate(
                system=INITIAL_STRATEGY_SYSTEM_PROMPT.format(
                    role=memory.self_role
                ),
                prompt=prompt,
            )
            print(f"[StrategyPlanGenerator] Generated Plan for {memory.self_name}")
            print(plan)
            return plan
        except Exception as e:
            print(f"[StrategyPlanGenerator] Failed to generate plan: {e}")
            return None

    def _build_prompt(self, memory: PlayerMemory) -> str:
        return f"""
You are {memory.self_name}.
Your role is: {memory.self_role}

Players in this game: {', '.join(memory.players)}

Think about your initial strategy carefully.
Consider your victory conditions, what actions you must avoid, and what actions are recommended to achieve your goal.

## Role-Specific Advice based on {memory.self_role}:
- If you are a **Werewolf**:
  - You can fake playing the Seer (`co_seer`) to mislead the village.
  - Or you can pretend to be a Villager (`co_villager`) to fly under the radar.
  - Staying silent (`silent`) is also a valid valid strategy if you want to avoid contradictions.
- If you are a **Madman**:
  - Your goal is to help the Werewolves win (or have the Werewolves survive, or be executed depending on specific rules, but generally support Evil).
  - Disrupt the discussion by faking Seer (`co_seer`) with false results.
  - Or claim Villager (`co_villager`) to reduce the suspect pool for Werewolves.
- If you are a **Seer**:
  - Usually, declaring yourself (`co_seer`) and sharing the truth is strong, but be careful of counter-claims.
- If you are a **Villager**:
  - Your info is limited. Deduce who is lying. `co_villager` is standard to clear yourself.

"""


# --- Global Instance ---
from src.config.llm import create_strategy_plan_llm

strategy_plan_generator = StrategyPlanGenerator(
    llm=create_strategy_plan_llm()
)
