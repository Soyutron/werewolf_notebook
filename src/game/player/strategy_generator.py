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

    設計原則:
    - StrategyPlan（全体戦略計画）は strategy_plan_generator.py が唯一の生成元
    - 本クラスは StrategyPlan を入力として受け取り、現在の状況に応じた
      具体的な行動指針（Action Guideline）のみを生成する
    - 独自に戦略を再解釈・再生成することは禁止
    - 戦略の一貫性は StrategyPlan によって担保される

    責務:
    - Action Guideline (Day): 議論フェーズごとの行動指針を生成
    - StrategyPlan を判断の一次情報として使用し、そこから逸脱しない
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
        
        # StrategyPlan が存在しない場合は警告（本来はNight Phaseで生成されているべき）
        if plan is None:
            print(f"[StrategyGenerator] WARNING: No StrategyPlan available for {memory.self_name}. Acting with degraded strategy.")
        
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
            recommended_actions_text = "\n".join(f"- {item}" for item in plan.recommended_actions) if plan.recommended_actions else "- (No specific recommendations)"
            strategy_section = f"""
==============================
YOUR STRATEGIC PLAN (SOURCE OF TRUTH)
==============================
This plan was decided at the start of the game. Your action guideline MUST align with this plan.
Do NOT reinterpret or override this strategy.

[Objective]
- Goal: {plan.initial_goal}
- Victory Condition: {plan.victory_condition}
- Defeat Condition: {plan.defeat_condition}

[Policy]
- Behavior: {plan.role_behavior}
- CO Policy: {plan.co_policy} (Intended CO Role: {plan.intended_co_role})

[RECOMMENDED ACTIONS]
{recommended_actions_text}

[MUST NOT DO]
{must_not_do_text}

Generate an action guideline that EXECUTES this plan based on the current situation.
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

[GUIDELINE FOR GENERATION]
1. Main Action: Decide the ONE most important action to take right now (trigger='immediate' or 'proactive').
   - If you want to CO, set action_type='co' and provide co_content.
   - If you want to vote/attack, set action_type='vote_inducement' or 'question'.
   - If nothing special, use 'observe'.

2. Conditional Actions: List actions to take IF specific things happen during this turn.
   - e.g. "If someone claims to be Seer (counter-co), I will counter-claim immediately."
   - e.g. "If I am heavily suspected, I will reveal my role."

3. Style: define the tone and focus of your speech.

Output JSON only conforming to the Strategy schema.
"""

# --- グローバルインスタンス ---
strategy_generator = StrategyGenerator(
    llm=create_strategy_llm()
)
