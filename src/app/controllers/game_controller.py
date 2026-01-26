"""
ゲームAPI - コントローラー

責務:
- エンドポイント定義
- HTTPリクエスト/レスポンスの処理
- エラーハンドリング
- セッション管理
"""

import traceback
import asyncio
import uuid
from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import JSONResponse
from rich.pretty import pprint

from src.app.schemas.game_responses import GameStartResponse, SpeakRequest
from src.app.services.game_service import GameService
from src.app.repositories import SessionRepository


router = APIRouter(prefix="/api/game", tags=["game"])


def _get_session_id(request: Request) -> str | None:
    """Cookie優先でセッションIDを取得し、無ければヘッダー X-Session-Id を見る"""
    return request.cookies.get("session_id") or request.headers.get("X-Session-Id")


@router.post("/start", response_model=GameStartResponse)
async def start_game(request: Request):
    """
    新規セッションで夜フェーズまで実行し、スナップショットを保存する。
    """

    async def run_game_with_timeout():
        try:
            # 新規セッションを作成
            session_id = str(uuid.uuid4())
            pprint(f"[GameController] New session created: {session_id}")

            # 夜フェーズ開始
            result = GameService.run_night(session_id=session_id)
            pprint(f"[GameController] Night response prepared successfully")

            return session_id, GameStartResponse(session_id=session_id, **result)

        except Exception as e:
            error_detail = traceback.format_exc()
            pprint(f"[GameController] Error occurred: {e}")
            pprint(f"[GameController] Traceback:\n{error_detail}")

            raise HTTPException(
                status_code=500,
                detail={
                    "status": "error",
                    "error": str(e),
                    "detail": error_detail,
                },
            )

    try:
        session_id, game_response = await asyncio.wait_for(run_game_with_timeout(), timeout=120.0)

        response = JSONResponse(content=game_response.model_dump())
        response.set_cookie(
            key="session_id",
            value=session_id,
            max_age=86400,
            httponly=True,
            samesite="lax",
        )

        pprint(f"[GameController] Session cookie set: {session_id}")
        return response

    except asyncio.TimeoutError:
        pprint(f"[GameController] Request timeout after 120 seconds")
        raise HTTPException(
            status_code=504,
            detail={
                "status": "error",
                "error": "Request timeout",
                "detail": "The game session took too long to complete. This may be due to API rate limits or network issues.",
            },
        )


@router.get("/state")
async def get_game_state(request: Request):
    """
    Cookie から セッション ID を取得してゲーム状態を復元

    Returns
    -------
    GameStartResponse
        保存されたゲーム状態
    """
    try:
        # Cookie からセッション ID を取得
        session_id = _get_session_id(request)

        if not session_id:
            raise HTTPException(
                status_code=400,
                detail={
                    "status": "error",
                    "error": "No session found",
                    "detail": "Please start a game first (/api/game/start)",
                },
            )

        pprint(f"[GameController] Retrieving session state: {session_id}")

        # Redis からセッション状態を取得
        result = SessionRepository.get(session_id)

        if not result:
            raise HTTPException(
                status_code=404,
                detail={
                    "status": "error",
                    "error": "Session not found",
                    "detail": f"Session {session_id} has expired or was not found. Please start a new game.",
                },
            )

        return GameStartResponse(session_id=session_id, **result)

    except HTTPException:
        raise
    except Exception as e:
        error_detail = traceback.format_exc()
        pprint(f"[GameController] Error occurred: {e}")
        pprint(f"[GameController] Traceback:\n{error_detail}")

        raise HTTPException(
            status_code=500,
            detail={
                "status": "error",
                "error": str(e),
                "detail": error_detail,
            },
        )


@router.post("/day", response_model=GameStartResponse)
async def run_day(request: Request, day_steps: int = 1):
    """
    昼フェーズを指定回数だけ進める。
    Cookie から session_id を取得し、Redis から復元したセッションで実行する。
    """

    async def run_day_with_timeout():
        try:
            session_id = _get_session_id(request)
            if not session_id:
                raise HTTPException(
                    status_code=400,
                    detail={
                        "status": "error",
                        "error": "No session found",
                        "detail": "Please start a game first (/api/game/start)",
                    },
                )

            result = GameService.run_day(session_id=session_id, day_steps=day_steps)

            if not result:
                raise HTTPException(
                    status_code=404,
                    detail={
                        "status": "error",
                        "error": "Session not found",
                        "detail": f"Session {session_id} has expired or was not found. Please start a new game.",
                    },
                )

            return session_id, GameStartResponse(session_id=session_id, **result)

        except HTTPException:
            raise
        except Exception as e:
            error_detail = traceback.format_exc()
            pprint(f"[GameController] Error occurred: {e}")
            pprint(f"[GameController] Traceback:\n{error_detail}")

            raise HTTPException(
                status_code=500,
                detail={
                    "status": "error",
                    "error": str(e),
                    "detail": error_detail,
                },
            )

    try:
        session_id, game_response = await asyncio.wait_for(run_day_with_timeout(), timeout=120.0)

        response = JSONResponse(content=game_response.model_dump())
        response.set_cookie(
            key="session_id",
            value=session_id,
            max_age=86400,
            httponly=True,
            samesite="lax",
        )
        return response

    except asyncio.TimeoutError:
        pprint(f"[GameController] Request timeout after 120 seconds (day)")
        raise HTTPException(
            status_code=504,
            detail={
                "status": "error",
                "error": "Request timeout",
                "detail": "The game session took too long to complete day steps.",
            },
        )


@router.post("/speak", response_model=GameStartResponse)
async def add_speak(request: Request, speak_data: SpeakRequest):
    """
    人間プレイヤーの発言をゲームに追加する。
    Cookie から session_id を取得し、Redis から復元したセッションで実行する。
    """
    try:
        session_id = _get_session_id(request)
        if not session_id:
            raise HTTPException(
                status_code=400,
                detail={
                    "status": "error",
                    "error": "No session found",
                    "detail": "Please start a game first (/api/game/start)",
                },
            )

        result = GameService.add_human_speak(
            session_id=session_id,
            player_name=speak_data.player_name,
            message=speak_data.message
        )

        if not result:
            raise HTTPException(
                status_code=404,
                detail={
                    "status": "error",
                    "error": "Session not found",
                    "detail": f"Session {session_id} has expired or was not found. Please start a new game.",
                },
            )

        response_model = GameStartResponse(session_id=session_id, **result)
        response = JSONResponse(content=response_model.model_dump())
        response.set_cookie(
            key="session_id",
            value=session_id,
            max_age=86400,
            httponly=True,
            samesite="lax",
        )
        return response

    except HTTPException:
        raise
    except Exception as e:
        error_detail = traceback.format_exc()
        pprint(f"[GameController] Error occurred: {e}")
        pprint(f"[GameController] Traceback:\n{error_detail}")

        raise HTTPException(
            status_code=500,
            detail={
                "status": "error",
                "error": str(e),
                "detail": error_detail,
            },
        )
