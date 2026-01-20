from typing import List, Dict, Optional
from pydantic import BaseModel, Field

# ==========================================
# 1. Strategy Plan (Static)
# ==========================================
class GMStrategyPlan(BaseModel):
    """
    夜フェーズで確定する、ゲーム全体を俯瞰した進行方針（固定情報）。
    書き換え禁止。
    """
    main_objective: str = Field(description="ゲーム全体を通したGMの主な目的・演出方針")
    key_scenarios: List[str] = Field(description="想定される主要な展開パターン（勝ち筋・負け筋の分岐点）")
    discussion_points: List[str] = Field(description="議論誘導のポイント（役職COの有無や矛盾が生じた際の介入指針）")

# ==========================================
# 2. Milestone Plan (Static)
# ==========================================
class GMMilestone(BaseModel):
    """
    議論や進行において期待する個別のシグナル・イベント。
    """
    id: str = Field(description="マイルストーンの一意なID")
    description: str = Field(description="マイルストーンの内容（例：占い師の対抗CO、初日の処刑決定など）")
    trigger_condition: str = Field(description="このマイルストーンが発生したとみなす条件")

class GMMilestonePlan(BaseModel):
    """
    マイルストーンの一覧（固定情報）。
    書き換え禁止。
    """
    milestones: List[GMMilestone] = Field(description="監視すべきマイルストーンのリスト")

# ==========================================
# 3. Milestone Status (Variable)
# ==========================================
class GMMilestoneStatus(BaseModel):
    """
    各マイルストーンの現在の状態（可変情報）。
    毎ターン更新。
    """
    status: Dict[str, str] = Field(
        description="マイルストーンIDとその状態（occurred / not_occurred / likely / unlikely など）のマッピング"
    )

# ==========================================
# 4. Policy Weights (Variable)
# ==========================================
class GMPolicyWeights(BaseModel):
    """
    現在の状況や参照結果から算出される判断用パラメータ（可変情報）。
    gm_comment_generator など、発話・介入判断の入力として使用。
    """
    intervention_level: int = Field(description="GMの介入度合い（1: 静観 〜 5: 強制介入）", ge=1, le=5)
    focus_player: Optional[str] = Field(description="現在GMが注目すべきプレイヤー（いれば）")
    humor_level: int = Field(description="ユーモアレベル（1: 真面目 〜 5: 冗談交じり）", ge=1, le=5, default=3)
    pacing_speed: int = Field(description="進行スピード（1: ゆっくり 〜 5: 急かす）", ge=1, le=5, default=3)


# ==========================================
# Root: GM Progression Plan
# ==========================================
class GMProgressionPlan(BaseModel):
    """
    GMの進行計画全体を表すモデル。
    固定部分と可変部分を包括する。
    """
    # Static Parts (Created at Night)
    strategy_plan: GMStrategyPlan
    milestone_plan: GMMilestonePlan

    # Variable Parts (Updated every turn)
    # 初期生成時は初期値が入る
    milestone_status: GMMilestoneStatus
    policy_weights: GMPolicyWeights

    def get_summary_markdown(self) -> str:
        """
        LLMプロンプト用に現在の計画状態をマークダウンで出力する。
        """
        lines = []
        lines.append(f"# GM Strategy: {self.strategy_plan.main_objective}")
        
        lines.append("\n## Milestones Status")
        for ms in self.milestone_plan.milestones:
            status = self.milestone_status.status.get(ms.id, "unknown")
            lines.append(f"- [{status}] {ms.description} (ID: {ms.id})")
        
        lines.append("\n## Current Policy Weights")
        lines.append(f"- Intervention: {self.policy_weights.intervention_level}")
        lines.append(f"- Pacing: {self.policy_weights.pacing_speed}")
        if self.policy_weights.focus_player:
            lines.append(f"- Focus: {self.policy_weights.focus_player}")
            
        return "\n".join(lines)
