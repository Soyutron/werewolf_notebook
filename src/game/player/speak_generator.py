# src/game/player/speak_generator.py
from typing import Optional, Union

from src.core.llm.client import LLMClient
from src.core.llm.prompts import SPEAK_SYSTEM_PROMPT
from src.core.memory.speak import Speak
from src.core.memory.strategy import Strategy
from src.core.types import PlayerMemory, GameEvent, PlayerRequest
from src.config.llm import create_speak_llm

Observed = Union[GameEvent, PlayerRequest]


class SpeakGenerator:
    """
    PlayerMemory と新しく観測した GameEvent / PlayerRequest から
    公開発言（Speak）を生成するクラス。

    設計方針:
    - 発言内容のみを生成する（state は変更しない）
    - 戦略（Strategy）が与えられた場合は、戦略に従った発言を生成する
    - 内省（Reflection）とは責務を分離
    - LLM が失敗しても None を返す
    """

    def __init__(self, llm: LLMClient):
        self.llm = llm

    def generate(
        self,
        *,
        memory: PlayerMemory,
        observed: Observed,
        strategy: Optional[Strategy] = None,
    ) -> Optional[Speak]:
        """
        発言を1件生成する。

        strategy が与えられた場合は、戦略に従った発言を生成する。
        失敗した場合は None を返す。
        """
        prompt = self._build_prompt(memory, observed, strategy)

        try:
            speak: Speak = self.llm.generate(
                system=SPEAK_SYSTEM_PROMPT,
                prompt=prompt,
            )

            print(speak)

            return speak

        except Exception:
            # 発言生成に失敗してもゲーム進行は止めない
            return None

    def _build_prompt(
        self,
        memory: PlayerMemory,
        observed: Observed,
        strategy: Optional[Strategy] = None,
    ) -> str:
        """
        発言生成用の user prompt を構築する。

        戦略が与えられた場合は、戦略のコンテキストをプロンプトに含める。
        co_decision が co_now の場合は CO を強制する。
        """
        observed_type = observed.__class__.__name__

        role_beliefs_text = "\n".join(
            f"- {player}: {belief.probs}"
            for player, belief in memory.role_beliefs.items()
        )

        recent_reflections_list = memory.history[-10:]
        recent_reflections = "\n".join(
            str(r) for r in reversed(recent_reflections_list)
        )

        # 戦略コンテキストの構築
        strategy_section = ""
        co_enforcement_section = ""
        
        if strategy is not None:
            # CO強制セクション（co_now の場合）
            if strategy.co_decision == "co_now":
                co_enforcement_section = f"""
==============================
MANDATORY CO (YOU MUST DO THIS)
==============================

Your strategy requires you to CO (Come Out) NOW.

Your speech MUST include ALL of the following:
1. 「私は占い師です」or equivalent CO statement
2. Target: {strategy.co_target}
3. Result: {strategy.co_result}

Example format:
「私は占い師です。{strategy.co_target}さんを占いました。結果は{strategy.co_result}でした。」

DO NOT skip the CO. DO NOT hint. STATE IT CLEARLY.
"""
            
            strategy_section = f"""
==============================
STRATEGY TO FOLLOW
==============================

Action Stance: {strategy.action_stance}
Main Claim: {strategy.main_claim}
Primary Target: {strategy.primary_target or "(none)"}

Goals:
{chr(10).join(f"- {goal}" for goal in strategy.goals)}

Approach:
{strategy.approach}

Key Points:
{chr(10).join(f"- {point}" for point in strategy.key_points)}
"""

        # 自己言及禁止のガード
        self_name = memory.self_name
        anti_self_ref_section = f"""
==============================
YOU ARE {self_name}
==============================

- Use first-person (私/俺/僕)
- NEVER say "{self_name}さん" or refer to yourself in third person
"""

        return f"""
{anti_self_ref_section}
{co_enforcement_section}
{strategy_section}

Recent observation:
Type: {observed_type}
Details: {observed.model_dump()}

Your beliefs (private):
{role_beliefs_text}

Recent thoughts:
{recent_reflections}

Generate a public statement. Output JSON only.
"""


# --- グローバルに1つだけ ---
speak_generator = SpeakGenerator(llm=create_speak_llm())
