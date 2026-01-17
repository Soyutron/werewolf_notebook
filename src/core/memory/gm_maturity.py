from pydantic import BaseModel


class GMMaturityDecision(BaseModel):
    """
    GM による議論成熟判定の結果
    """

    is_mature: bool
    reason: str
