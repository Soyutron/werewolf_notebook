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
        # Speak counts and last speaker logic
        speak_counts = {p: 0 for p in players}
        last_speaker = None
        for event in public_events:
            if event.event_type == "speak":
                speaker = event.payload.get("player")
                if speaker in speak_counts:
                    speak_counts[speaker] += 1
                last_speaker = speaker

        # Format speaking stats
        stats_lines = []
        for p in players:
            count = speak_counts.get(p, 0)
            stats_lines.append(f"- {p}: {count}回")
        stats_text = "\n".join(stats_lines)
        last_speaker_text = f"Last Speaker: {last_speaker}" if last_speaker else "Last Speaker: None"

        combined_review = (
            f"主要な指摘:\n{review.reason}\n\n補足:\n{review.fix_instruction}"
        )
        context_str = format_events(list(reversed(public_events)))
        user_prompt = f"""
Context (Public Events):
{context_str}

Player Status:
{stats_text}

{last_speaker_text}

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
