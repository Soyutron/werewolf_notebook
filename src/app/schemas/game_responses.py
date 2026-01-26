"""
ゲームAPI - レスポンススキーマ定義

責務:
- リクエスト・レスポンスのデータ構造定義
- Pydantic BaseModel を用いた型安全性の確保
"""

from typing import Dict, Any
from pydantic import BaseModel


class GameStartResponse(BaseModel):
    """ゲーム開始レスポンス"""
    session_id: str
    definition: Dict[str, Any]
    world_state: Dict[str, Any]
    player_states: Dict[str, Dict[str, Any]]


class SpeakRequest(BaseModel):
    """発言投稿リクエスト"""
    player_name: str
    message: str
