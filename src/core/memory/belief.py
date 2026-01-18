from typing import List
from pydantic import BaseModel
from src.core.types import PlayerName


class RoleProbOutput(BaseModel):
    """
    vLLM grammar 対応のための固定フィールド構造。
    Dict[RoleName, float] だと propertyNames エラーが出る可能性があるため。
    """
    villager: float
    seer: float
    werewolf: float
    madman: float


class PlayerBeliefItem(BaseModel):
    player: PlayerName
    belief: RoleProbOutput


class RoleBeliefsOutput(BaseModel):
    """
    LLM が生成する role_beliefs の出力専用モデル。

    NOTE:
    - vLLM の grammar 生成で Dict (additionalProperties) がエラーになるため List を使用
    - 正規化・検証は呼び出し側の責務
    """

    beliefs: List[PlayerBeliefItem]
