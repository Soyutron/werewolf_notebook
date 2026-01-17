from src.core.types import PlayerOutput, PlayerState
from src.game.player.vote_generator import vote_generator


def handle_vote(state: PlayerState) -> PlayerState:
    """
    投票要求を受け取り、投票先を決定するノード。
    """
    print("handle_vote")

    request = state["input"].request
    memory = state["memory"]

    vote = None

    if request is not None:
        vote = vote_generator.generate(
            memory=memory,
            observed=request,
        )
        if vote is not None:
            memory.history.append(vote)

    # 投票アクションを返す
    state["output"] = PlayerOutput(
        action="vote",
        payload={
            "target": vote.target if vote is not None else None,
        },
    )

    print(state)
    return state
