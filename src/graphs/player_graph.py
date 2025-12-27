from src.core.types import PlayerState


class DummyPlayerGraph:
    """
    仮の PlayerGraph
    ・input.request をそのまま output に変換するだけ
    ・設計検証用
    """

    def invoke(self, state: PlayerState) -> PlayerState:
        request = state.input.get("request")

        if request is None:
            state.output = None
            return state

        state.output = {
            "action": request["request_type"],
            "payload": request["payload"],
        }
        return state


# 仮の compiled_player_graph
compiled_player_graph = DummyPlayerGraph()
