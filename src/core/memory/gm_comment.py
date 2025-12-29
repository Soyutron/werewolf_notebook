# src/core/memory/gm_comment.py
from typing import TypedDict
from src.core.types import PlayerName


class GMComment(TypedDict):
    """
    GM が生成する公開コメント。

    - speaker : 次に発言するプレイヤー
    - text    : 議論を整理しつつ指名するコメント
    """

    speaker: PlayerName
    text: str
