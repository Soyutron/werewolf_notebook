# src/core/memory/strategy.py
from typing import List, Optional, Literal, Dict
from pydantic import BaseModel, Field


# ===========================================
# 1. Milestone (固定情報)
# ===========================================
class PlayerMilestone(BaseModel):
    """
    議論において期待する個別のシグナル・イベント。
    strategy_plan から導出される。
    """
    id: str = Field(description="マイルストーンの一意なID")
    description: str = Field(description="期待するシグナルの内容（例: '誰かが占いCOする', '対抗COが発生する'）")
    trigger_condition: str = Field(description="このマイルストーンが発生とみなされる条件")
    importance: Literal["high", "medium", "low"] = Field(
        default="medium",
        description="重要度（戦略に与える影響の大きさ）"
    )


class PlayerMilestonePlan(BaseModel):
    """
    マイルストーンの一覧（固定情報）。
    戦略計画から導出され、ゲーム中は書き換え禁止。
    """
    milestones: List[PlayerMilestone] = Field(
        default_factory=list,
        description="監視すべきマイルストーンのリスト"
    )


# ===========================================
# 2. Milestone Status (可変情報)
# ===========================================
class PlayerMilestoneStatus(BaseModel):
    """
    各マイルストーンの現在の状態（可変情報）。
    議論フェーズごと、またはターンごとに更新される。
    """
    status: Dict[str, Literal["not_occurred", "occurred", "strong", "weak"]] = Field(
        default_factory=dict,
        description="マイルストーンIDとその状態のマッピング"
    )


# ===========================================
# 3. Policy Weights (可変情報)
# ===========================================
class PlayerPolicyWeights(BaseModel):
    """
    milestone_status の参照結果から動的に算出される重み。
    発言方針の調整にのみ使用する。
    speak_generator の入力として利用する。
    """
    aggression: int = Field(
        default=5, ge=1, le=10,
        description="攻撃性 (1: 防御的・穏便 〜 10: 攻撃的・断定的)"
    )
    trust_building: int = Field(
        default=5, ge=1, le=10,
        description="信頼構築 (1: 疑念優先 〜 10: 信頼構築優先)"
    )
    information_reveal: int = Field(
        default=5, ge=1, le=10,
        description="情報開示度 (1: 秘匿 〜 10: 積極的に情報開示)"
    )
    urgency: int = Field(
        default=5, ge=1, le=10,
        description="緊急度 (1: 慎重・様子見 〜 10: 急いで行動)"
    )
    focus_player: Optional[str] = Field(
        default=None,
        description="現在注目すべきプレイヤー（いれば）"
    )


# ===========================================
# 4. Strategy Plan (固定情報)
# ===========================================
class StrategyPlan(BaseModel):
    """
    ゲーム全体を通じた長期的な戦略計画（Night Phaseで生成）。
    ゲーム中は一切書き換えを行わない。
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
    co_policy: Literal[
        "co_seer",       # 占い師としてCOする
        "co_villager",   # 村人としてCOする
        "wait_and_see",  # 様子見（後出しジャンケン）
        "counter_co",    # 対抗COが出たらCOする
    ] = Field(
        description="CO（カミングアウト）に関する基本方針"
    )
    intended_co_role: Optional[Literal["seer", "villager", "werewolf", "madman"]] = Field(
        default=None,
        description="COする予定の役職（COしない場合はNone）"
    )
    
    # マイルストーン計画（戦略から導出される固定情報）
    milestone_plan: PlayerMilestonePlan = Field(
        default_factory=PlayerMilestonePlan,
        description="戦略計画から導出される、議論中に観測したい期待シグナルの一覧"
    )


# ===========================================
# 5. Structured Action & Strategy (New)
# ===========================================

ActionTrigger = Literal[
    "immediate",          # 今すぐ実行する（Main Action用）
    "proactive",          # 自分から能動的に動く
    "reactive_counter",   # 対抗COが出現した場合
    "reactive_suspicion", # 自分や仲間が疑われた場合
    "reactive_vote",      # 投票誘導があった場合
    "observation",        # 特定の条件を監視する
]

ActionType = Literal[
    "co",                 # カミングアウト
    "vote_inducement",    # 投票誘導
    "question",           # 質問・詰問
    "agree",              # 同意・便乗
    "disagree",           # 反論・否定
    "observe",            # 様子見・静観
    "skip",               # 特になし
]

class COContent(BaseModel):
    """
    CO（カミングアウト）を行う際の詳細情報
    """
    role: Literal["seer", "medium", "bodyguard", "villager", "werewolf", "madman"] = Field(
        description="COする役職"
    )
    result: Optional[str] = Field(
        default=None,
        description="結果がある場合の内容（例: '安西先生は人狼', '白'）"
    )
    target: Optional[str] = Field(
        default=None,
        description="結果の対象プレイヤー"
    )
    reason: Optional[str] = Field(
        default=None,
        description="COする理由（発言生成のヒント）"
    )

class TurnAction(BaseModel):
    """
    1ターンにおける具体的な行動単位。
    メイン行動としても、条件付き行動としても使用できる。
    """
    action_type: ActionType = Field(description="行動の種類")
    trigger: ActionTrigger = Field(description="行動のトリガー条件")
    target_player: Optional[str] = Field(default=None, description="行動の対象")
    description: str = Field(description="行動の具体的な内容・指示")
    
    # オプション: COする場合の詳細
    co_content: Optional[COContent] = Field(default=None, description="COする場合の詳細情報")
    
    # オプション: 投票誘導や疑念向けの場合の強さ
    pressure: int = Field(default=5, ge=1, le=10, description="圧力・強さ (1-10)")


class Strategy(BaseModel):
    """
    議論フェーズごとの具体的な行動指針（Action Guideline）。
    StrategyPlanに基づき、そのターンの状況に合わせて生成される。
    
    [変更点]
    フラグ管理のCOではなく、メイン行動と条件付き行動のリストとして再定義。
    """
    kind: Literal["strategy"] = "strategy"
    
    # 1. Main Action: このターンで最も優先すべき行動
    main_action: TurnAction = Field(
        description="このターンの主体となる行動（通常は trigger='immediate' または 'proactive'）"
    )
    
    # 2. Conditional Actions: 特定の条件が満たされた場合に発動する行動
    # 例: "対抗COが出たら即座に反論する", "自分に投票が集まりそうならCOする"
    conditional_actions: List[TurnAction] = Field(
        default=[],
        description="条件付きその他行動（優先順）"
    )
    
    # 3. Tone / Style Parameters (以前のパラメータを整理)
    style_focus: Literal["logic", "emotion", "trust", "aggression"] = Field(
        default="logic",
        description="発言の重視点"
    )
    text_style: str = Field(
        description="文体や口調の指示（例: '冷静に', '感情的に', '混乱した様子で'）"
    )

    # 4. Status Awareness (旧 doubt_level 等の代わりに状況認識を含める)
    current_priority: str = Field(
        description="現在の最優先事項（例: '潜伏して生き延びる', '偽占い師を破綻させる'）"
    )
    
    def get_co_action(self) -> Optional[TurnAction]:
        """
        COを含むアクションがあれば返す（Main優先）
        """
        if self.main_action.action_type == "co":
            return self.main_action
        for action in self.conditional_actions:
            if action.action_type == "co":
                return action
        return None


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
