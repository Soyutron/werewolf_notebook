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
        from src.core.roles import get_role_advice

        return f"""
You are {memory.self_name}.
Your role is: {memory.self_role}

Players in this game: {', '.join(memory.players)}

Think about your initial strategy carefully.
Consider your victory conditions, what actions you must avoid, and what actions are recommended to achieve your goal.

## Role-Specific Advice based on {memory.self_role}:
{get_role_advice(memory.self_role)}
"""


# --- Global Instance ---
from src.config.llm import create_strategy_plan_llm

strategy_plan_generator = StrategyPlanGenerator(
    llm=create_strategy_plan_llm()
)
