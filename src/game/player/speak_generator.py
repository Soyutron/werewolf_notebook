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
        """
        observed_type = observed.__class__.__name__

        role_beliefs_text = "\n".join(
            f"- {player}: {belief.probs}"
            for player, belief in memory.role_beliefs.items()
        )

        recent_reflections_list = memory.history[-15:]
        # Reverse to show newest first
        recent_reflections = "\n".join(
            str(r) for r in reversed(recent_reflections_list)
        )

        # 戦略コンテキストの構築
        if strategy is not None:
            strategy_section = f"""
==============================
STRATEGY TO FOLLOW (CRITICAL)
==============================

You have already decided on a strategy. Your speech MUST align with this strategy.

Selected Strategy: {strategy.selected_option_name}
Action Type: {strategy.action_type}

Goals:
{chr(10).join(f"- {goal}" for goal in strategy.goals)}

Approach:
{strategy.approach}

Key Points (MUST be reflected in your speech):
{chr(10).join(f"- {point}" for point in strategy.key_points)}

IMPORTANT: Your speech must follow the above strategy exactly.
Do NOT contradict the key points.
Do NOT take actions that conflict with the approach.
"""
        else:
            strategy_section = ""

        # 自己言及禁止のガード（最上位に配置）
        self_name = memory.self_name
        anti_self_ref_section = f"""
==============================
CRITICAL: YOU ARE {self_name}
==============================

- You are speaking as {self_name}
- Use first-person (私/俺/僕)
- NEVER say "{self_name}さん" or refer to yourself in third person
- This is YOUR OWN statement
"""

        return f"""
{anti_self_ref_section}

You are speaking publicly in a Werewolf-style game.
{strategy_section}
Recent observation:
Type: {observed_type}
Details:
{observed.model_dump()}

Your current beliefs (private, do not reveal directly):
{role_beliefs_text}

Your recent internal reflections:
{recent_reflections}

Rules:
- Speak naturally, as a human player.
- Do NOT reveal your exact role unless forced.
- If a strategy is provided above, your speech MUST follow it exactly.
- Do NOT mention probabilities or internal state.
- Output JSON only.

Generate a public statement.
"""


# --- グローバルに1つだけ ---
speak_generator = SpeakGenerator(llm=create_speak_llm())
