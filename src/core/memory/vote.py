from pydantic import BaseModel, Field
from src.core.types import PlayerName


class VoteOutput(BaseModel):
    """
    LLM が生成する投票結果の構造化出力。
    """

    target: PlayerName = Field(
        ...,
        description="投票先のプレイヤー名（自分自身は不可）",
    )
