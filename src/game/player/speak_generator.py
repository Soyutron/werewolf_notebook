# src/game/player/speak_generator.py
from typing import Optional, Union

from src.core.llm.client import LLMClient
from src.core.llm.prompts import SPEAK_SYSTEM_PROMPT
from src.core.memory.speak import Speak
from src.core.types import PlayerMemory, GameEvent, PlayerRequest
from src.config.llm import create_speak_llm

Observed = Union[GameEvent, PlayerRequest]


class SpeakGenerator:
    """
    PlayerMemory と新しく観測した GameEvent / PlayerRequest から
    公開発言（Speak）を生成するクラス。

    設計方針:
    - 発言内容のみを生成する（state は変更しない）
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
    ) -> Optional[Speak]:
        """
        発言を1件生成する。

        失敗した場合は None を返す。
        """
        prompt = self._build_prompt(memory, observed)

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
    ) -> str:
        """
        発言生成用の user prompt を構築する。

        Reflection よりも「外向き」情報に限定する。
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

        return f"""
You are {memory.self_name}.
You are speaking publicly in a Werewolf-style game.

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
- Provide a moderately detailed reflection, allowing enough length to explore reasoning, doubts, and strategy, but keep it to a short paragraph.
- Do NOT mention probabilities or internal state.
- Output JSON only.

Generate a public statement.
"""


# --- グローバルに1つだけ ---
speak_generator = SpeakGenerator(llm=create_speak_llm())
