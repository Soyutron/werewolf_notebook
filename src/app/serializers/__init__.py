"""
シリアライザーパッケージ

責務:
- ドメインモデル ↔ 辞書の変換
- シリアライズ / デシリアライズロジックの集約
"""

from src.app.serializers.game_serializer import GameSerializer

__all__ = ["GameSerializer"]
