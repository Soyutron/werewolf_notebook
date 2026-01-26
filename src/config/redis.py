"""
Redis 設定

責務:
- Redis クライアント初期化
- コネクション管理
"""

import os
import redis
from typing import Optional

class RedisClient:
    """Redis クライアント管理"""

    _instance: Optional[redis.Redis] = None

    @classmethod
    def get_client(cls) -> redis.Redis:
        """Redis クライアントの取得（シングルトン）"""
        if cls._instance is None:
            host = os.getenv("REDIS_HOST", "localhost")
            port = int(os.getenv("REDIS_PORT", 6379))
            db = int(os.getenv("REDIS_DB", 0))

            cls._instance = redis.Redis(
                host=host,
                port=port,
                db=db,
                decode_responses=True,  # 自動的に文字列にデコード
                socket_connect_timeout=5,
            )

            # 接続確認
            try:
                cls._instance.ping()
                print(f"[Redis] Connected to {host}:{port}")
            except Exception as e:
                print(f"[Redis] Connection failed: {e}")
                raise

        return cls._instance

    @classmethod
    def close(cls):
        """Redis クライアントのクローズ"""
        if cls._instance is not None:
            cls._instance.close()
            cls._instance = None
