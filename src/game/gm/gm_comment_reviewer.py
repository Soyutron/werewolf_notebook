# src/game/gm/gm_comment_reviewer.py
from src.core.llm.client import LLMClient
from src.core.llm.prompts import GM_COMMENT_REVIEW_SYSTEM_PROMPT
from src.core.memory.gm_comment import GMComment
from src.core.types import GameEvent
from src.config.llm import create_gm_comment_reviewer_llm
from src.core.memory.gm_comment_review import GMCommentReviewResult


def format_events_for_review(
    events: list[GameEvent],
    *,
    limit: int = 15,
) -> str:
    """
    GMコメントレビュー用に public_event を整形する。
    Reviewer が判断に必要な最低限の情報のみ渡す。
    """
    recent_events = events[-limit:]
    return "\n".join(f"- [{e.event_type}] {e.payload}" for e in recent_events)


class GMCommentReviewer:
    """
    生成済み GMComment が
    現在の議論状況に照らして適切かをレビューする。

    Reviewer の責務:
    - 事実矛盾・不自然な誘導の検出
    - ゲーム性を壊す GM 発言の抑制
    - 表現の個性や曖昧さは尊重する
    """

    def __init__(self, llm: LLMClient):
        self.llm = llm

    def review(
        self,
        *,
        comment: GMComment,
        public_events: list[GameEvent],
        players: list[str],
    ) -> GMCommentReviewResult:
        """
        GMComment をレビューする。
        """

        events_text = format_events_for_review(list(reversed(public_events)))

        prompt = self._build_prompt(
            comment=comment,
            events_text=events_text,
        )

        try:
            response = self.llm.generate(
                system=GM_COMMENT_REVIEW_SYSTEM_PROMPT,
                prompt=prompt,
            )

            # レスポンスは既に GMCommentReviewResult 型としてパースされている
            return response

        except Exception:
            return GMCommentReviewResult(
                needs_fix=False,
                reason="review_failed",
            )

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
""".strip()


# --- グローバルに1つだけ ---
gm_comment_reviewer = GMCommentReviewer(llm=create_gm_comment_reviewer_llm())
