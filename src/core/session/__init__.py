"""
session パッケージ - ゲーム実行セッション関連

後方互換性のため、既存の `from src.core.session import GameSession` を
そのまま動作させるための集約モジュール。

モジュール構成:
- game_session.py   : GameSession クラス（state の唯一所有者）
- action_resolver.py: PlayerOutput → 副作用解釈
- dispatcher.py     : GameDecision → state 反映
- phase_runner.py   : フェーズ進行制御
"""

from src.core.session.game_session import GameSession
from src.core.session.action_resolver import ActionResolver
from src.core.session.dispatcher import Dispatcher
from src.core.session.phase_runner import PhaseRunner

__all__ = [
    "GameSession",
    "ActionResolver",
    "Dispatcher",
    "PhaseRunner",
]
