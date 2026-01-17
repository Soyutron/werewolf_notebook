# src/game/player/speak_refiner.py
from typing import Optional

from src.core.llm.client import LLMClient
from src.core.llm.prompts import SPEAK_REFINE_SYSTEM_PROMPT
from src.core.memory.strategy import Strategy, SpeakReview
from src.core.memory.speak import Speak
from src.core.types.player import PlayerMemory
from src.config.llm import create_speak_refiner_llm


class SpeakRefiner:
    """
    レビュー指摘を反映して発言を修正するクラス。

    設計方針:
    - 最小限の変更で修正を行う
    - 戦略の key_points に沿った内容を維持
    - 自然な日本語を維持
    """

    def __init__(self, llm: LLMClient):
        self.llm = llm

    def refine(
        self,
        *,
        original: Speak,
        strategy: Strategy,
        review: SpeakReview,
        memory: PlayerMemory,
    ) -> Optional[Speak]:
        """
        発言をリファインする。

        失敗した場合は None を返す。
        """
        prompt = self._build_prompt(original, strategy, review, memory)

        try:
            refined: Speak = self.llm.generate(
                system=SPEAK_REFINE_SYSTEM_PROMPT,
                prompt=prompt,
            )
            print(f"[SpeakRefiner] Refined speech for {memory.self_name}")
            print(refined)
            return refined

        except Exception as e:
            print(f"[SpeakRefiner] Failed to refine speech: {e}")
            return None

    def _build_prompt(
        self,
        original: Speak,
        strategy: Strategy,
        review: SpeakReview,
        memory: PlayerMemory,
    ) -> str:
        """
        リファイン用のプロンプトを構築する。
        """
        # 自己言及禁止のガード（最上位に配置）
        self_name = memory.self_name
        valid_partners = [p for p in memory.players if p != self_name]
        
        return f"""
==============================
CRITICAL: YOU ARE {self_name}
==============================

- You are speaking as {self_name}
- Use first-person (私/俺/僕)
- NEVER say "{self_name}さん" or refer to yourself in third person
- NEVER use vague pronouns ("彼", "彼女", "あの人", "そいつ"). ALWAYS use specific names.

Player: {self_name}
Role: {memory.self_role}
Valid Partners: {valid_partners}

Strategy to follow:
- Goals: {strategy.goals}
- Approach: {strategy.approach}
- Key Points: {strategy.key_points}

Original Speech:
"{original.text}"

Review Feedback:
- Reason: {review.reason}
- Fix Instruction: {review.fix_instruction}

Refine the speech to address the fix instruction.
Apply minimal changes while preserving the original tone.
Output JSON only.
"""


# --- グローバルインスタンス ---
speak_refiner = SpeakRefiner(llm=create_speak_refiner_llm())
