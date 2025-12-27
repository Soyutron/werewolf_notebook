# game/gm/dispatch.py
from src.core.types import PlayerInput, PlayerRequest
from src.core.session import GameSession


def dispatch_use_ability(
    session: GameSession,
    *,
    player: str,
    candidates: list[str],
):
    """
    夜フェーズ：
    指定プレイヤーに能力使用の機会を与える
    """

    request: PlayerRequest = {
        "request_type": "use_ability",
        "payload": {
            "candidates": candidates,
        },
    }

    input: PlayerInput = {
        "request": request,
    }

    return session.run_player_turn(
        player=player,
        input=input,
    )

def dispatch_speech(
    session: GameSession,
    *,
    player: str,
    topic: str,
):
    request: PlayerRequest = {
        "request_type": "speak",
        "payload": {
            "topic": topic,
        },
    }

    input: PlayerInput = {
        "request": request,
    }

    return session.run_player_turn(
        player=player,
        input=input,
    )

def dispatch_vote(
    session: GameSession,
    *,
    player: str,
    candidates: list[str],
):
    request: PlayerRequest = {
        "request_type": "vote",
        "payload": {
            "candidates": candidates,
        },
    }

    input: PlayerInput = {
        "request": request,
    }

    return session.run_player_turn(
        player=player,
        input=input,
    )
