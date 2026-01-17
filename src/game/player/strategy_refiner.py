# src/game/player/strategy_refiner.py
from typing import Optional

from src.core.llm.client import LLMClient
from src.core.llm.prompts import STRATEGY_REFINE_SYSTEM_PROMPT
from src.core.memory.strategy import Strategy, StrategyReview
from src.core.types.player import PlayerMemory
from src.config.llm import create_strategy_refiner_llm


class StrategyRefiner:
    """
    レビュー指摘を反映して戦略を修正するクラス。

    設計方針:
    - 最小限の変更で修正を行う
    - 元の意図を保持する
    - 指摘された問題のみを解決する
    """

    def __init__(self, llm: LLMClient):
        self.llm = llm

    def refine(
        self,
        *,
        original: Strategy,
        review: StrategyReview,
        memory: PlayerMemory,
    ) -> Optional[Strategy]:
        """
        戦略をリファインする。

        失敗した場合は None を返す。
        """
        prompt = self._build_prompt(original, review, memory)

        try:
            refined: Strategy = self.llm.generate(
                system=STRATEGY_REFINE_SYSTEM_PROMPT,
                prompt=prompt,
            )
            print(f"[StrategyRefiner] Refined strategy for {memory.self_name}")
            print(refined)
            return refined

        except Exception as e:
            print(f"[StrategyRefiner] Failed to refine strategy: {e}")
            return None

    def _build_prompt(
        self, original: Strategy, review: StrategyReview, memory: PlayerMemory
    ) -> str:
        """
        リファイン用のプロンプトを構築する。
        """
        return f"""
Player: {memory.self_name}
Role: {memory.self_role}

Original Strategy:
- Goals: {original.goals}
- Approach: {original.approach}
- Key Points: {original.key_points}

Review Feedback:
- Reason: {review.reason}
- Fix Instruction: {review.fix_instruction}

Refine the strategy to address the fix instruction.
Apply minimal changes while preserving the original intent.
Output JSON only.
"""


# --- グローバルインスタンス ---
strategy_refiner = StrategyRefiner(llm=create_strategy_refiner_llm())
