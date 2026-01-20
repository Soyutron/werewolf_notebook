# src/game/player/strategy_generator.py
from typing import Optional, Dict

from src.core.llm.client import LLMClient
from src.core.llm.prompts.strategy import get_strategy_system_prompt
from src.core.memory.strategy import Strategy, StrategyPlan
from src.core.types.player import PlayerMemory
from src.config.llm import create_strategy_llm


class StrategyGenerator:
    """
    プレイヤーの議論フェーズごとの行動指針（Local Strategy）を生成するクラス。

    責務:
    - Action Guideline (Day): 議論フェーズごとの行動指針を生成
    - 戦略計画書 (StrategyPlan) を判断の一次情報として使用する。
    """

    def __init__(self, llm: LLMClient):
        self.llm = llm

    def generate_action_guideline(
        self,
        *,
        memory: PlayerMemory,
        plan: Optional[StrategyPlan] = None,
    ) -> Optional[Strategy]:
        """
        [Discussion Phase] 現在の状況と戦略計画に基づき、行動指針を生成する。
        """
        # plan が指定されていない場合は memory から取得
        if plan is None:
            plan = memory.strategy_plan
        
        role = memory.self_role
        system_prompt = get_strategy_system_prompt(role)

        prompt = self._build_guideline_prompt(memory, plan)

        try:
            strategy: Strategy = self.llm.generate(
                system=system_prompt,
                prompt=prompt,
            )
            print(f"[StrategyGenerator] Generated Action Guideline for {memory.self_name}")
            print(strategy)
            return strategy

        except Exception as e:
            print(f"[StrategyGenerator] Failed to generate action guideline: {e}")
            return None

    def _build_guideline_prompt(self, memory: PlayerMemory, plan: Optional[StrategyPlan]) -> str:
        """
        行動指針生成用のプロンプトを構築する。
        """
        # 1. Game Context (Static / Semi-static)
        players_list = ", ".join(memory.players)
        
        # 2. Strategy Plan (The Source of Truth)
        strategy_section = ""
        if plan:
            must_not_do_text = "\n".join(f"- {item}" for item in plan.must_not_do)
            strategy_section = f"""
==============================
YOUR STRATEGIC PLAN
==============================
[Objective]
- Goal: {plan.initial_goal} (Victory: {plan.victory_condition})
- Defeat Impact: {plan.defeat_condition}

[Policy]
- Behavior: {plan.role_behavior}
- CO Policy: {plan.co_policy} (Intended CO: {plan.intended_co_role})

[MUST NOT DO]
{must_not_do_text}

Act according to this plan while adapting to the immediate situation.
"""
        else:
            strategy_section = "(No strategic plan available. Act based on role.)"

        # 3. Private Knowledge (e.g., Seer Result)
        private_knowledge = ""
        if memory.self_role == "seer":
            for event in memory.observed_events:
                if event.event_type == "divine_result":
                   private_knowledge = f"\n[Private Knowledge] Divination Result: {event.payload.get('target')} is {event.payload.get('result')}.\n" 
                   break

        # 4. Current Situation (Dynamic)
        # ログ要約と履歴を使用
        log_summary = memory.log_summary if memory.log_summary else "(No discussion summary yet)"
        
        # 直近のイベント (最新1件のみ表示して即時反応を促す、あるいは完全に削除)
        # ユーザー要望は「リストを渡さない」なので、ここも基本はSummaryに任せる。
        # ただし、Summaryに含まれていない「たった今」の出来事があるかもしれないが、
        # LogSummarizerが直前に走っている前提なら不要。
        # 安全のため、"Last Event" として1件だけ出すか、あるいは完全に消すか。
        # 方針: 完全にSummaryに任せる。
        
        return f"""
Are you {memory.self_name} ({memory.self_role}).
Players: {players_list}
{private_knowledge}
{strategy_section}

==============================
CURRENT SITUATION
==============================
[Summary]
{log_summary}

Based on your Strategic Plan and the Current Situation, generate your next action guideline.
Output JSON only.
"""

# --- グローバルインスタンス ---
strategy_generator = StrategyGenerator(
    llm=create_strategy_llm()
)
