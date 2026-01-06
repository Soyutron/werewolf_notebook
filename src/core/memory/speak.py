# src/core/memory/speak.py
from pydantic import BaseModel, Field


class Speak(BaseModel):
    """
    プレイヤーの公開発言。
    他プレイヤー・GM から観測される。
    """

    kind: str = Field(default="speak")
    text: str
