# src/game/gm/gm_policy_weights_calculator.py
"""
GM 判断用パラメータ（Policy Weights）算出コンポーネント。

責務:
- milestone_status から policy_weights を動的に算出する
- gm_comment_generator の入力として利用される
"""
from typing import Optional

from src.core.memory.gm_plan import (
    GMMilestonePlan,
    GMMilestoneStatus,
    GMPolicyWeights,
    GMStrategyPlan,
)


class GMPolicyWeightsCalculator:
    """
    milestone_status から policy_weights を算出する。

    設計原則:
    - milestone_status（可変）と strategy_plan（固定）を入力とする
    - 状況に応じて介入レベルや進行スピードなどを調整する
    """

    def calculate(
        self,
        milestone_plan: GMMilestonePlan,
        milestone_status: GMMilestoneStatus,
        strategy_plan: Optional[GMStrategyPlan] = None,
    ) -> GMPolicyWeights:
        """
        マイルストーン状態から Policy Weights を算出する。
        """
        # デフォルト値
        intervention = 3
        pacing = 3
        humor = 3
        focus_player: Optional[str] = None

        if not milestone_plan.milestones:
            return GMPolicyWeights(
                intervention_level=intervention,
                pacing_speed=pacing,
                humor_level=humor,
                focus_player=focus_player,
            )

        occurred_count = 0
        total_milestones = len(milestone_plan.milestones)
        
        for milestone in milestone_plan.milestones:
            status = milestone_status.status.get(milestone.id, "not_occurred")
            if status in ("occurred", "strong"):
                occurred_count += 1

        # 単純なロジック例:
        # マイルストーンが多く達成されるほど、ゲームは終盤に近づく → ペーシングを上げる
        if total_milestones > 0:
            progress_ratio = occurred_count / total_milestones
            if progress_ratio > 0.5:
                pacing = 4
            if progress_ratio > 0.8:
                pacing = 5

        # もし特定の「トラブル」や「停滞」を示唆するマイルストーンがあれば介入度を上げるなどのロジックをここに追加可能
        # 現状はシンプルに

        # 戦略プランからの調整（もしあれば）
        # strategy_plan.main_objective の内容によってベースを変えるなど

        return GMPolicyWeights(
            intervention_level=intervention,
            pacing_speed=pacing,
            humor_level=humor,
            focus_player=focus_player,
        )

    def get_default_weights(self) -> GMPolicyWeights:
        """
        デフォルトの重みを取得する。
        """
        return GMPolicyWeights(
            intervention_level=3,
            pacing_speed=3,
            humor_level=3,
            focus_player=None,
        )


# --- グローバルインスタンス ---
gm_policy_weights_calculator = GMPolicyWeightsCalculator()
