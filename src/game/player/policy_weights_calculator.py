# src/game/player/policy_weights_calculator.py
"""
発言方針重み算出コンポーネント。

責務:
- milestone_status から policy_weights を動的に算出する
- 発言方針の調整にのみ使用される
- speak_generator の入力として利用される
"""
from typing import Optional

from src.core.memory.strategy import (
    PlayerMilestonePlan,
    PlayerMilestoneStatus,
    PlayerPolicyWeights,
    StrategyPlan,
)


class PolicyWeightsCalculator:
    """
    milestone_status から policy_weights を算出する。

    設計原則:
    - milestone_status（可変）を読み取り、policy_weights（可変）を算出
    - strategy_plan の情報も考慮して重みを調整
    - 算出結果は speak_generator で発言のトーン調整に使用
    """

    def calculate(
        self,
        milestone_plan: PlayerMilestonePlan,
        milestone_status: PlayerMilestoneStatus,
        strategy_plan: Optional[StrategyPlan] = None,
    ) -> PlayerPolicyWeights:
        """
        マイルストーン状態から発言方針重みを算出する。

        Args:
            milestone_plan: マイルストーン計画（固定）
            milestone_status: 現在のマイルストーン状態（可変）
            strategy_plan: 戦略計画（固定、参考情報）

        Returns:
            算出された発言方針重み
        """
        # デフォルト値から開始
        aggression = 5
        trust_building = 5
        information_reveal = 5
        urgency = 5
        focus_player: Optional[str] = None

        if not milestone_plan.milestones:
            return PlayerPolicyWeights(
                aggression=aggression,
                trust_building=trust_building,
                information_reveal=information_reveal,
                urgency=urgency,
                focus_player=focus_player,
            )

        # マイルストーンの発生状況に基づいて重みを調整
        high_occurred = 0
        medium_occurred = 0
        total_occurred = 0

        for milestone in milestone_plan.milestones:
            status = milestone_status.status.get(milestone.id, "not_occurred")

            if status in ("occurred", "strong", "weak"):
                total_occurred += 1

                if milestone.importance == "high":
                    high_occurred += 1
                elif milestone.importance == "medium":
                    medium_occurred += 1

                # strong シグナルの場合は追加の調整
                if status == "strong":
                    urgency += 1
                    aggression += 1

        # 重要なマイルストーンが発生した場合の調整
        if high_occurred > 0:
            # 重要なイベントが発生 → 緊急度と攻撃性を上げる
            urgency = min(10, urgency + high_occurred * 2)
            aggression = min(10, aggression + high_occurred)
            # 情報開示も増やす（状況が動いているため）
            information_reveal = min(10, information_reveal + high_occurred)

        # 中程度のマイルストーンが発生した場合の調整
        if medium_occurred > 0:
            urgency = min(10, urgency + medium_occurred)
            trust_building = min(10, trust_building + medium_occurred)

        # 戦略計画からの調整
        if strategy_plan:
            # CO方針が immediate の場合は情報開示を上げる
            if strategy_plan.co_policy == "immediate":
                information_reveal = min(10, information_reveal + 2)

            # 潜伏系の行動方針の場合は信頼構築を重視
            if "潜伏" in strategy_plan.role_behavior or "様子見" in strategy_plan.role_behavior:
                trust_building = min(10, trust_building + 1)
                aggression = max(1, aggression - 1)

            # 攻撃的な行動方針の場合
            if "攻撃" in strategy_plan.role_behavior or "追い詰める" in strategy_plan.role_behavior:
                aggression = min(10, aggression + 2)

        # 値の正規化（1-10の範囲に収める）
        return PlayerPolicyWeights(
            aggression=max(1, min(10, aggression)),
            trust_building=max(1, min(10, trust_building)),
            information_reveal=max(1, min(10, information_reveal)),
            urgency=max(1, min(10, urgency)),
            focus_player=focus_player,
        )

    def get_default_weights(self) -> PlayerPolicyWeights:
        """
        デフォルトの発言方針重みを取得する。
        """
        return PlayerPolicyWeights()


# --- グローバルインスタンス ---
policy_weights_calculator = PolicyWeightsCalculator()
