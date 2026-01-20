from typing import List
from pydantic import BaseModel
from src.core.types import PlayerName


from pydantic import create_model
from src.core.roles import get_all_role_names

# RoleProbOutput を動的に生成
# vLLM grammar 対応のため、現在登録されている全役職をフィールドとして持つモデルを作成
# equivalent to:
# class RoleProbOutput(BaseModel):
#     villager: float = 0.0
#     seer: float = 0.0
#     ...
roles = {role: (float, 0.0) for role in get_all_role_names()}
RoleProbOutput = create_model('RoleProbOutput', **roles)


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
