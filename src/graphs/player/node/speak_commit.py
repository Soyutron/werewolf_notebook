# src/graphs/player/node/speak_commit.py
from src.core.types.player import PlayerState, PlayerOutput


def speak_commit_node(state: PlayerState) -> PlayerState:
    """
    確定した発言を output に設定し、history に追加するノード。

    責務:
    - internal.pending_speak を PlayerOutput に変換
    - memory.history に発言を追加
    - state["output"] を設定
    """
    print("[speak_commit_node] Committing speech...")

    memory = state["memory"]
    internal = state["internal"]
    pending_speak = internal.pending_speak

    if pending_speak is None:
        print("[speak_commit_node] No pending speech to commit")
        state["output"] = None
        return state

    # history に追加
    memory.history.append(pending_speak)

    # output を設定
    state["output"] = PlayerOutput(
        action="speak",
        payload={
            "text": pending_speak.text,
        },
    )

    print(f"[speak_commit_node] Speech committed: {pending_speak.text[:50]}...")

    return state
