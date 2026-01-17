# src/game/player/strategy_reviewer.py
from typing import Optional

from src.core.llm.client import LLMClient
from src.core.llm.prompts import STRATEGY_REVIEW_SYSTEM_PROMPT
from src.core.memory.strategy import Strategy, StrategyReview
from src.core.types.player import PlayerMemory
from src.config.llm import create_strategy_reviewer_llm


class StrategyReviewer:
    """
    生成された戦略をレビューするクラス。

    設計方針:
    - 戦略が役職の目標に沿っているかをチェック
    - 実行可能性を検証
    - 論理的整合性を確認
    """

    def __init__(self, llm: LLMClient):
        self.llm = llm

    def review(
        self,
        *,
        strategy: Strategy,
        memory: PlayerMemory,
    ) -> Optional[StrategyReview]:
        """
        戦略をレビューする。

        失敗した場合は None を返す（安全側に倒す = commit）。
        """
        prompt = self._build_prompt(strategy, memory)

        try:
            result: StrategyReview = self.llm.generate(
                system=STRATEGY_REVIEW_SYSTEM_PROMPT,
                prompt=prompt,
            )
            print(f"[StrategyReviewer] Review result: needs_fix={result.needs_fix}")
            print(result)
            return result

        except Exception as e:
            print(f"[StrategyReviewer] Failed to review strategy: {e}")
            return None

    def _build_prompt(self, strategy: Strategy, memory: PlayerMemory) -> str:
        """
        レビュー用のプロンプトを構築する。
        """
        return f"""
Player: {memory.self_name}
Role: {memory.self_role}

Strategy to review:
- Goals: {strategy.goals}
- Approach: {strategy.approach}
- Key Points: {strategy.key_points}

Review this strategy for the given role.
Output JSON only.
"""


# --- グローバルインスタンス ---
strategy_reviewer = StrategyReviewer(llm=create_strategy_reviewer_llm())
