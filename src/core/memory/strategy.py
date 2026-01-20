# src/core/memory/strategy.py
from typing import List, Optional, Literal
from pydantic import BaseModel, Field


class StrategyPlan(BaseModel):
    """
    ゲーム全体を通じた長期的な戦略計画（Night Phaseで生成）。
    """
    kind: Literal["strategy_plan"] = "strategy_plan"

    initial_goal: str = Field(
        description="このゲームにおける最終的な勝利条件・目標（例: '占い師として信頼を勝ち取る', '人狼として処刑を回避する'）"
    )
    victory_condition: str = Field(
        description="勝利するために必要な具体的な状態や条件（例: '人狼を処刑する際に、自分が生存していること'）"
    )
    defeat_condition: str = Field(
        description="敗北につながる状態や条件（例: '初日に処刑される', '人狼と疑われる'）"
    )
    role_behavior: str = Field(
        description="役職としての振る舞い方針（例: '潜伏して情報を集める', '積極的にCOして場を乱す'）"
    )
    must_not_do: List[str] = Field(
        default=[],
        description="絶対に避けるべき行動や展開のリスト（例: ['矛盾した発言をする', '寡黙になりすぎる']）"
    )
    recommended_actions: List[str] = Field(
        default=[],
        description="戦略を達成するために推奨される行動のリスト（例: ['積極的に質問を投げかける', '疑わしいプレイヤーに投票を誘導する']）"
    )
    co_policy: Literal["immediate", "wait_and_see", "no_co", "counter_co"] = Field(
        description="CO（カミングアウト）に関する基本方針"
    )
    intended_co_role: Optional[Literal["seer", "villager", "werewolf", "madman"]] = Field(
        default=None,
        description="COする予定の役職（COしない場合はNone）"
    )


class Strategy(BaseModel):
    """
    議論フェーズごとの具体的な行動指針（Action Guideline）。
    StrategyPlanに基づき、そのターンの状況に合わせて生成される。
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
    
    # === 戦略パラメータ（抽象） ===
    # 自然言語ではなく、パラメータで方針を決定する
    
    target_player: Optional[str] = Field(
        default=None,
        description="このターンの主なターゲット（攻撃・質問・保護対象）"
    )
    
    value_focus: Literal["logic", "emotion", "trust", "aggression"] = Field(
        default="logic",
        description="発言の重視点: logic=論理矛盾の指摘, emotion=感情への訴え, trust=信用形成, aggression=攻撃性"
    )

    aggression_level: int = Field(
        description="攻撃性パラメータ (1-10): 1=防御的・穏便, 10=超攻撃的・断定"
    )
    
    doubt_level: int = Field(
        description="疑念の強さ (1-10): 1=信じている, 10=完全に疑っている（嘘つき扱い）"
    )
    
    action_type: Literal["co", "agree", "disagree", "question", "vote_inducement", "skip"] = Field(
        description="具体的な行動タイプ"
    )
    
    style_instruction: str = Field(
        description="発言のスタイルの指示（例: '冷静に事実を並べる', '困惑した様子で問いかける', '断定的に追い詰める'）"
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
