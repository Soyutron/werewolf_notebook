from typing import Protocol
from src.core.types import PlayerState
from copy import deepcopy
from src.graphs.player_graph import PlayerGraph


class PlayerController(Protocol):
    """
    プレイヤーに行動させるためのインターフェース
    （人間 / AI の違いを吸収する）
    """

    def act(
        self,
        *,
        state: PlayerState,
    ) -> PlayerState: ...


class AIPlayerController:
    """
    AI プレイヤー用 Controller
    PlayerGraph（思考エンジン）を使って行動を決定する
    """

    def __init__(self, player_graph: PlayerGraph):
        self.player_graph = player_graph

    def act(
        self,
        *,
        state: PlayerState,
    ) -> PlayerState:
        working_state = deepcopy(state)
        new_state = self.player_graph.invoke(working_state)
        return new_state
