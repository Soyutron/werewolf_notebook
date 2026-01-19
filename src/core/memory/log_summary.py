# src/core/memory/log_summary.py
"""
ログ要約の出力モデル

責務:
- LLMによる差分ログ要約の結果を表現
"""

from pydantic import BaseModel, Field


class LogSummaryOutput(BaseModel):
    """
    ログ要約LLMの出力スキーマ。
    
    差分要約の結果を構造化された形式で返す。
    """
    
    updated_summary: str = Field(
        description="既存の要約に新しい情報を統合した結果。"
        "重要な発言、CO情報、投票傾向、主要な対立構造などを含む。"
    )
    
    key_events: list[str] = Field(
        default_factory=list,
        description="今回追加されたイベントの中で特に重要なもののリスト"
    )
