# src/core/memory/strategy.py
from typing import List, Optional, Literal
from pydantic import BaseModel, Field


class Strategy(BaseModel):
    """
    プレイヤーの発言前戦略（軽量版）。
    
    設計方針:
    - LLM出力コスト削減のため、複雑なネスト構造を排除
    - アクション指向のシンプルな構造
    - 占い師のCO判断を明示的にサポート
    """

    kind: Literal["strategy"] = "strategy"
    
    # === CO判断（占い師・人狼・狂人向け） ===
    co_decision: Optional[Literal["co_now", "co_later", "no_co"]] = Field(
        default=None,
        description="CO判断: co_now=即CO, co_later=様子見, no_co=COしない"
    )
    co_target: Optional[str] = Field(
        default=None,
        description="CO時に結果を伝える対象プレイヤー名"
    )
    co_result: Optional[str] = Field(
        default=None,
        description="CO時に伝える結果（例: '人狼', '村人'）"
    )
    
    # === 基本方針 ===
    action_type: Literal["co", "analysis", "question", "hypothesize", "line_formation", "vote_inducement", "summarize_situation"] = Field(
        default="vote_inducement",
        description="行動タイプ: co=CO, analysis=分析共有, question=質問, hypothesize=仮説提示, line_formation=ライン形成, vote_inducement=投票誘導, summarize_situation=状況整理"
    )
    action_stance: Literal["aggressive", "defensive", "neutral"] = Field(
        description="発言の基本スタンス"
    )
    primary_target: Optional[str] = Field(
        default=None,
        description="主に言及・追及するプレイヤー名"
    )
    main_claim: str = Field(
        description="この発言で伝えたい核心メッセージ（1文）"
    )
    
    # === 具体的なアクション（speak_generator互換） ===
    goals: List[str] = Field(
        description="この戦略における具体的な達成目標リスト"
    )
    approach: str = Field(
        description="目標達成のための具体的なアプローチ・振る舞い"
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
