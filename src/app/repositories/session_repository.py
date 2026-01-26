"""
セッションリポジトリ

責務:
- ゲームセッションの Redis への保存/取得
- データ永続化の詳細を隠蔽
"""

import json
from typing import Dict, Any, Optional
from rich.pretty import pprint

from src.config.redis import RedisClient


class SessionRepository:
    """ゲームセッションの永続化を担当するリポジトリ"""

    @staticmethod
    def save(session_id: str, snapshot: Dict[str, Any], ttl: int = 86400) -> None:
        """
        セッションスナップショットを Redis に保存

        Parameters
        ----------
        session_id : str
            セッション ID
        snapshot : Dict[str, Any]
            ゲーム結果＋内部状態（assigned_roles / gm_internal を含む）
        ttl : int
            有効期限（秒）、デフォルト: 86400秒（24時間）
        """
        try:
            redis_client = RedisClient.get_client()

            # JSON にシリアライズして保存
            redis_client.setex(
                f"game:session:{session_id}:definition",
                ttl,
                json.dumps(snapshot["definition"], ensure_ascii=False),
            )
            redis_client.setex(
                f"game:session:{session_id}:world_state",
                ttl,
                json.dumps(snapshot["world_state"], ensure_ascii=False),
            )
            redis_client.setex(
                f"game:session:{session_id}:player_states",
                ttl,
                json.dumps(snapshot["player_states"], ensure_ascii=False),
            )

            # 内部状態も保存（復元用）
            redis_client.setex(
                f"game:session:{session_id}:assigned_roles",
                ttl,
                json.dumps(snapshot.get("assigned_roles"), ensure_ascii=False),
            )
            redis_client.setex(
                f"game:session:{session_id}:gm_internal",
                ttl,
                json.dumps(snapshot.get("gm_internal"), ensure_ascii=False),
            )

            pprint(f"[SessionRepository] Session {session_id} saved to Redis (TTL: {ttl}s)")

        except Exception as e:
            pprint(f"[SessionRepository] Failed to save session to Redis: {e}")
            # Redis が利用できない場合でもゲームは続行

    @staticmethod
    def get(session_id: str) -> Optional[Dict[str, Any]]:
        """
        Redis からセッションスナップショットを取得

        Parameters
        ----------
        session_id : str
            セッション ID

        Returns
        -------
        Optional[Dict[str, Any]]
            セッションスナップショット、または存在しない場合は None
        """
        try:
            redis_client = RedisClient.get_client()

            definition = redis_client.get(f"game:session:{session_id}:definition")
            world_state = redis_client.get(f"game:session:{session_id}:world_state")
            player_states = redis_client.get(f"game:session:{session_id}:player_states")
            assigned_roles = redis_client.get(f"game:session:{session_id}:assigned_roles")
            gm_internal = redis_client.get(f"game:session:{session_id}:gm_internal")

            if not (definition and world_state and player_states):
                pprint(f"[SessionRepository] Session {session_id} not found in Redis")
                return None

            result = {
                "definition": json.loads(definition),
                "world_state": json.loads(world_state),
                "player_states": json.loads(player_states),
            }

            # 追加の内部情報（再開専用）
            if assigned_roles:
                result["assigned_roles"] = json.loads(assigned_roles)
            if gm_internal:
                result["gm_internal"] = json.loads(gm_internal)

            pprint(f"[SessionRepository] Session {session_id} retrieved from Redis")
            return result

        except Exception as e:
            pprint(f"[SessionRepository] Failed to retrieve session from Redis: {e}")
            return None
