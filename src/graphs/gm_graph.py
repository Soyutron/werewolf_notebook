# graphs/gm_graph.py
from src.core.types import GMState
from src.game.gm.dispatch import dispatch_vote


def gm_vote_node(state: GMState) -> GMState:
    """
    GMGraph の node
    ・state を見て判断するだけ
    ・「誰に投票させたいか」を state に書く
    """

    requests = []

    for player in state["players"]:
        candidates = [p for p in state["players"] if p != player]

        requests.append(
            {
                "type": "vote",
                "player": player,
                "candidates": candidates,
            }
        )

    state["pending_requests"] = requests
    return state
