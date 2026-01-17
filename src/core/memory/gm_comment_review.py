from pydantic import BaseModel
from typing import Optional


class GMCommentReviewResult(BaseModel):
    """
    GM コメントのレビュー結果。

    reviewer は「判断」のみを行う。
    文章の生成・修正は一切行わない。
    """

    needs_fix: bool
    reason: str
    fix_instruction: Optional[str] = None
