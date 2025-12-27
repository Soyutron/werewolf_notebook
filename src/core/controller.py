from typing import Protocol, Optional
from src.core.types import PlayerOutput, PlayerState


class PlayerController(Protocol):
    """
    プレイヤーに行動させるためのインターフェース
    （人間 / AI の違いを吸収する）
    """

    def act(
        self,
        *,
        state: PlayerState,
    ) -> Optional[PlayerOutput]: ...


class AIPlayerController:
    """
    AI プレイヤー用 Controller
    PlayerGraph を使って思考させる
    """

    def __init__(self, player_graph):
        self.player_graph = player_graph

    def act(
        self,
        *,
        state: PlayerState,
    ) -> Optional[PlayerOutput]:
        new_state = self.player_graph.invoke(state)
        return new_state["output"]
