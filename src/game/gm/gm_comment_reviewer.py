# src/game/gm/gm_comment_reviewer.py
from typing import Optional

from src.core.llm.client import LLMClient
from src.core.llm.prompts import GM_COMMENT_REVIEW_SYSTEM_PROMPT
from src.core.memory.gm_comment import GMComment
from src.core.types import GameEvent
from src.config.llm import create_gm_comment_reviewer_llm


def format_events_for_review(events: list[GameEvent]) -> str:
    """
    GMコメントレビュー用に public_event を整形する。
    """
    return "\n".join(f"- [{e.event_type}] {e.payload}" for e in events)


class GMCommentReviewer:
    """
    生成済み GMComment が
    現在の議論状況に照らして適切かをレビューする。

    - 問題がなければ None を返す
    - 修正が必要な場合のみ修正済み GMComment を返す
    """

    def __init__(self, llm: LLMClient):
        self.llm = llm

    def review(
        self,
        *,
        comment: GMComment,
        public_events: list[GameEvent],
    ) -> Optional[GMComment]:
        """
        GMComment をレビューする。
        """

        # ★ 直近15件のみを見る（Generator と揃える）
        recent_events = public_events[-15:]
        events_text = format_events_for_review(recent_events)

        prompt = self._build_prompt(
            comment=comment,
            events_text=events_text,
        )

        try:
            response = self.llm.generate(
                system=GM_COMMENT_REVIEW_SYSTEM_PROMPT,
                prompt=prompt,
            )

            # LLM が「修正不要」と判断した場合は None を返す想定
            # （JSON の設計次第だが、None or same-text 判定を想定）
            if response is None:
                return None

            return response

        except Exception:
            # レビュー失敗時は原文を採用（進行を止めない）
            return None

    def _build_prompt(
        self,
        *,
        comment: GMComment,
        events_text: str,
    ) -> str:
        """
        GMコメントレビュー用 prompt を構築する。
        """
        return f"""
Current GM Comment:
Speaker: {comment.speaker}
Text:
{comment.text}

Recent public events:
{events_text}
"""


# --- グローバルに1つだけ ---
gm_comment_reviewer = GMCommentReviewer(
    llm=create_gm_comment_reviewer_llm()
)
