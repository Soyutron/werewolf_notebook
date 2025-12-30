# src/core/memory/gm_comment.py
from pydantic import BaseModel
from src.core.types import PlayerName


class GMComment(BaseModel):
    """
    GM が生成する公開コメント。

    - speaker : 次に発言するプレイヤー
    - text    : 議論を整理しつつ指名するコメント
    """

    speaker: PlayerName
    text: str
