from src.core.types import PlayerState, PlayerOutput
from typing import Protocol


class PlayerGraph(Protocol):
    """
    Player の思考エンジンの共通インターフェース
    （LangGraph / Dummy / Test 用など）
    """

    def invoke(self, state: PlayerState) -> PlayerState: ...


class DummyPlayerGraph:
    """
    仮の PlayerGraph
    ・input.request をそのまま output に変換するだけ
    ・設計検証用
    """

    def invoke(self, state: PlayerState) -> PlayerState:
        request = state["input"].request

        if request is None:
            state["output"] = None
            return state

        state["output"] = PlayerOutput(
            action=request.request_type,
            payload=request.payload,
        )
        return state


# 仮の PlayerGraph
player_graph = DummyPlayerGraph()
