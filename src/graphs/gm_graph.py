# graphs/gm_graph.py
from src.core.types import GMState
from src.game.gm.dispatch import dispatch_vote

def gm_vote_node(state: GMState) -> GMState:
    """
    GMGraph の node
    ・state を見て判断
    ・dispatch を呼ぶ
    ・state を更新して返す
    """

    for player in state["players"]:
        candidates = [p for p in state["players"] if p != player]

        dispatch_vote(
            session=session,  # 外部から注入
            player=player,
            candidates=candidates,
        )

    return state