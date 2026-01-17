from src.core.memory.gm_comment import GMComment
from pydantic import BaseModel
from typing import Optional


class GMCommentReviewResult(BaseModel):
    """
    GMコメントレビュー結果。

    - needs_fix=False:
        修正不要 or レビュー失敗（原文を採用）
    - needs_fix=True:
        comment を採用する
    """

    needs_fix: bool
    comment: Optional[GMComment] = None
    reason: Optional[str] = None  # デバッグ・分析用（進行には不使用）
