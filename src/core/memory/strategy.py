# src/core/memory/strategy.py
from typing import List, Optional, Literal
from pydantic import BaseModel, Field


class RoleAssumption(BaseModel):
    """役職・陣営に基づく前提整理"""

    role_objective: str = Field(description="自分の役職における本来の目的")
    allies_enemies: str = Field(description="味方陣営と対立陣営の認識")
    winning_condition: str = Field(description="勝利条件の定義")


class SituationAnalysis(BaseModel):
    """状況分析"""

    public_info: str = Field(description="公開情報の分析（発言、CO、投票など）")
    private_info: str = Field(description="非公開情報の分析（自分の役職、夜の行動結果など）")
    constraints: str = Field(description="意思決定に与える制約・前提条件")


class StrategicOption(BaseModel):
    """検討した戦略的選択肢"""

    name: str = Field(description="戦略名（例: 正直にCO、潜伏、対抗CO）")
    pros: str = Field(description="メリット")
    cons: str = Field(description="デメリット・リスク")
    evaluation: str = Field(description="現状との適合度評価")


class Strategy(BaseModel):
    """
    プレイヤーの発言前戦略。
    
    思考過程、分析、選択肢の検討を含めた包括的な戦略定義。
    """

    kind: Literal["strategy"] = "strategy"
    
    # 1. 前提整理
    role_assumptions: RoleAssumption = Field(description="役職に基づく前提")
    
    # 2. 状況分析
    situation_analysis: SituationAnalysis = Field(description="現状の分析")
    
    # 3. 選択肢の検討
    considered_options: List[StrategicOption] = Field(description="検討した選択肢のリスト")
    
    # 4. 決定事項
    selected_option_name: str = Field(description="選択した戦略の名前")
    action_type: Literal["fixed", "tentative"] = Field(
        description="戦略の確定度（fixed: 確定行動, tentative: 暫定方針）"
    )
    
    # 5. 具体的なアクション（既存フィールドの維持・活用）
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
