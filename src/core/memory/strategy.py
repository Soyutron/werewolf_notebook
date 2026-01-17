# src/core/memory/strategy.py
from typing import List, Optional, Literal
from pydantic import BaseModel, Field


class Strategy(BaseModel):
    """
    プレイヤーの発言前戦略。

    発言（Speak）の前に立てる戦略的な計画を表す。
    - 役職に応じた目標設定
    - アプローチ方法
    - 発言に含めるべきポイント
    """

    kind: Literal["strategy"] = "strategy"
    goals: List[str] = Field(
        description="達成したい目標のリスト（例: 信頼を得る、疑惑をそらす）"
    )
    approach: str = Field(
        description="目標達成のためのアプローチ方法"
    )
    key_points: List[str] = Field(
        description="発言に含めるべき具体的なポイント"
    )


class StrategyReview(BaseModel):
    """
    戦略のレビュー結果。

    戦略が役職の目標に沿っているか、
    ゲーム状況に適切かをチェックした結果。
    """

    needs_fix: bool = Field(
        description="修正が必要な場合は True"
    )
    reason: str = Field(
        description="レビュー結果の理由"
    )
    fix_instruction: Optional[str] = Field(
        default=None,
        description="修正が必要な場合の指示（needs_fix=False の場合は None）"
    )


class SpeakReview(BaseModel):
    """
    発言のレビュー結果。

    発言が戦略に沿っているか、
    ゲームルールに違反していないかをチェックした結果。
    """

    needs_fix: bool = Field(
        description="修正が必要な場合は True"
    )
    reason: str = Field(
        description="レビュー結果の理由"
    )
    fix_instruction: Optional[str] = Field(
        default=None,
        description="修正が必要な場合の指示（needs_fix=False の場合は None）"
    )
