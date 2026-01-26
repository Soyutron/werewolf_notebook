"""
ゲーム実行サービス

責務:
- ゲームセッションの実行オーケストレーション
- 夜/昼フェーズの進行制御
- セッション復元と状態管理の調整
"""

from typing import Dict, Any, Optional
from rich.pretty import pprint

from src.core.session import GameSession
from src.game.one_night import ONE_NIGHT_GAME_DEFINITION
from src.graphs.gm.gm_graph import gm_graph
from src.graphs.player.player_graph import player_graph
from src.core.controller import AIPlayerController, PlayerController
from src.core.types import GameEvent
from src.app.serializers import GameSerializer
from src.app.repositories import SessionRepository


class GameService:
    """ゲーム実行のオーケストレーションを担当するサービス"""

    @staticmethod
    def _create_controllers(players: list[str]) -> dict[str, PlayerController]:
        """プレイヤーリストから AIPlayerController 辞書を生成"""
        return {player: AIPlayerController(player_graph) for player in players}

    @staticmethod
    def _build_payload_and_snapshot(session: GameSession) -> tuple[Dict[str, Any], Dict[str, Any]]:
        """
        セッションからクライアント返却用ペイロードと Redis 保存用スナップショットを生成

        Returns
        -------
        tuple[Dict[str, Any], Dict[str, Any]]
            (response_payload, snapshot)
        """
        response_payload = {
            "definition": GameSerializer.serialize_game_definition(session.definition),
            "world_state": GameSerializer.serialize_world_state(session.world_state),
            "player_states": {
                player: GameSerializer.serialize_player_state(state)
                for player, state in session.player_states.items()
            },
        }

        snapshot = {
            **response_payload,
            "assigned_roles": session.assigned_roles,
            "gm_internal": session.gm_internal.model_dump(),
        }

        return response_payload, snapshot

    @staticmethod
    def restore_session(snapshot: Dict[str, Any]) -> GameSession:
        """
        Redis スナップショットから GameSession インスタンスを復元

        Parameters
        ----------
        snapshot : Dict[str, Any]
            Redis から取得したスナップショット

        Returns
        -------
        GameSession
            復元されたゲームセッション
        """
        definition = GameSerializer.deserialize_game_definition(snapshot["definition"])
        world_state = GameSerializer.deserialize_world_state(snapshot["world_state"])
        player_states = {
            player: GameSerializer.deserialize_player_state(state)
            for player, state in snapshot.get("player_states", {}).items()
        }

        controllers = GameService._create_controllers(world_state.players)
        assigned_roles = snapshot.get("assigned_roles", {})
        gm_internal = GameSerializer.deserialize_gm_internal(snapshot.get("gm_internal", {}))

        return GameSession(
            definition=definition,
            world_state=world_state,
            player_states=player_states,
            controllers=controllers,
            assigned_roles=assigned_roles,
            gm_graph=gm_graph,
            gm_internal=gm_internal,
        )

    @staticmethod
    def run_night(session_id: str) -> Dict[str, Any]:
        """
        新規セッションで夜フェーズまでを実行し、Redis に保存する。
        """
        session = GameSession.create(definition=ONE_NIGHT_GAME_DEFINITION)

        pprint(f"[GameService] Running night phase...")
        session.run_night_phase()
        pprint(f"[GameService] Night phase completed")

        response_payload, snapshot = GameService._build_payload_and_snapshot(session)
        SessionRepository.save(session_id, snapshot)
        return response_payload


    @staticmethod
    def run_day(session_id: str, day_steps: int = 1) -> Optional[Dict[str, Any]]:
        """
        Redis に保存されたセッションを復元し、昼フェーズを指定回数実行して保存する。
        """
        snapshot = SessionRepository.get(session_id)
        if not snapshot:
            return None

        session = GameService.restore_session(snapshot)

        # 必要なら昼に入る前の夜をスキップ/実行
        if session.world_state.phase == "night":
            session.run_night_phase()

        pprint(f"[GameService] Running {day_steps} day steps...")
        for i in range(day_steps):
            pprint(f"[GameService] Day step {i+1}/{day_steps}")
            session.run_day_step()

        response_payload, snapshot = GameService._build_payload_and_snapshot(session)
        SessionRepository.save(session_id, snapshot)
        return response_payload

    @staticmethod
    def add_human_speak(session_id: str, player_name: str, message: str) -> Optional[Dict[str, Any]]:
        """
        人間プレイヤーの発言をゲームに追加し、状態を更新する。

        Parameters
        ----------
        session_id : str
            セッション ID
        player_name : str
            発言するプレイヤー名
        message : str
            発言内容

        Returns
        -------
        Optional[Dict[str, Any]]
            更新後のゲーム状態、またはセッションが存在しない場合は None
        """
        snapshot = SessionRepository.get(session_id)
        if not snapshot:
            return None

        session = GameService.restore_session(snapshot)

        # 発言イベントを作成
        speak_event = GameEvent(
            event_type="speak",
            payload={
                "player": player_name,
                "text": message,
            }
        )

        # public_events に追加（全員に共有）
        session.world_state.public_events.append(speak_event)

        # 各プレイヤーの observed_events にも追加
        for player, state in session.player_states.items():
            state["memory"].observed_events.append(speak_event)

        pprint(f"[GameService] Human speak added: {player_name}: {message}")

        response_payload, snapshot = GameService._build_payload_and_snapshot(session)
        SessionRepository.save(session_id, snapshot)
        return response_payload
