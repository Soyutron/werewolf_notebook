from typing import Optional
import traceback

from src.core.llm.client import LLMClient
from src.core.llm.prompts import GM_COMMENT_REFINE_SYSTEM_PROMPT
from src.core.memory.gm_comment import GMComment
from src.core.memory.gm_comment_review import GMCommentReviewResult
from src.core.types import GameEvent, PlayerName
from src.config.llm import create_gm_comment_refiner_llm


def format_events(events: list[GameEvent]) -> str:
    return "\n".join(f"- [{e.event_type}] {e.payload}" for e in events)


class GMCommentRefiner:
    """
    GM コメントをレビュー指摘を踏まえて修正・再生成するクラス。

    設計思想:
    - 既存の GMComment を必ず入力として受け取る
    - レビュー指摘を「満たすこと」を最優先する
    - 新規生成ではなく「修正」であることを明示する
    """

    def __init__(self, llm: LLMClient):
        self.llm = llm

    def refine(
        self,
        *,
        original: GMComment,
        review: GMCommentReviewResult,
        public_events: list[GameEvent],
        players: list[PlayerName],
    ) -> Optional[GMComment]:
        
        combined_review = (
            f"主要な指摘:\n{review.reason}\n\n補足:\n{review.fix_instruction}"
        )
        context_str = format_events(list(reversed(public_events)))
        user_prompt = f"""
Context (Public Events):
{context_str}

Original GM Comment:
{original}

Review Feedback:
{combined_review}

Please refine the GM comment based on the feedback.
"""

        try:
            response = self.llm.generate(
                system=GM_COMMENT_REFINE_SYSTEM_PROMPT,
                prompt=user_prompt,
            )
            print(response)
            return response
        except Exception:
            traceback.print_exc()
            return None


# singleton
gm_comment_refiner = GMCommentRefiner(llm=create_gm_comment_refiner_llm())
