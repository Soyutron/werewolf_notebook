from typing import Dict
from pydantic import BaseModel
from src.core.types import PlayerName, RoleProb


class RoleBeliefsOutput(BaseModel):
    """
    LLM が生成する role_beliefs の出力専用モデル。

    NOTE:
    - RoleProb は使わない（LLM 出力は生の確率 dict）
    - 正規化・検証は呼び出し側の責務
    """

    beliefs: Dict[PlayerName, RoleProb]
