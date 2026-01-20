"""
Unit tests for Player Strategy Structure.

Tests verify the new data models for player strategy planning:
- PlayerMilestone / PlayerMilestonePlan (固定)
- PlayerMilestoneStatus / PlayerPolicyWeights (可変)
- StrategyPlan with milestone_plan field
"""
import sys
from src.core.memory.strategy import (
    PlayerMilestone,
    PlayerMilestonePlan,
    PlayerMilestoneStatus,
    PlayerPolicyWeights,
    StrategyPlan,
)


# ===========================================
# Mock Data
# ===========================================
MOCK_MILESTONE = PlayerMilestone(
    id="ms_co_declaration",
    description="誰かが役職COする",
    trigger_condition="COイベントが発生",
    importance="high"
)

MOCK_MILESTONE_PLAN = PlayerMilestonePlan(
    milestones=[MOCK_MILESTONE]
)

MOCK_MILESTONE_STATUS = PlayerMilestoneStatus(
    status={"ms_co_declaration": "not_occurred"}
)

MOCK_POLICY_WEIGHTS = PlayerPolicyWeights(
    aggression=7,
    trust_building=4,
    information_reveal=6,
    urgency=5,
    focus_player="Alice"
)

MOCK_STRATEGY_PLAN = StrategyPlan(
    initial_goal="占い師として信頼を勝ち取る",
    victory_condition="人狼を処刑する際に生存していること",
    defeat_condition="初日に処刑される",
    role_behavior="積極的にCOして情報を共有",
    must_not_do=["矛盾した発言をする"],
    recommended_actions=["積極的に質問を投げかける"],
    co_policy="co_seer",
    intended_co_role="seer",
    milestone_plan=MOCK_MILESTONE_PLAN
)


# ===========================================
# Tests
# ===========================================
def test_player_milestone_structure():
    """PlayerMilestone の構造検証"""
    ms = MOCK_MILESTONE
    assert ms.id == "ms_co_declaration"
    assert ms.description == "誰かが役職COする"
    assert ms.trigger_condition == "COイベントが発生"
    assert ms.importance == "high"
    print("[PASS] test_player_milestone_structure")


def test_player_milestone_plan_structure():
    """PlayerMilestonePlan の構造検証"""
    plan = MOCK_MILESTONE_PLAN
    assert len(plan.milestones) == 1
    assert plan.milestones[0].id == "ms_co_declaration"
    print("[PASS] test_player_milestone_plan_structure")


def test_player_milestone_status_structure():
    """PlayerMilestoneStatus の構造検証（可変情報）"""
    status = MOCK_MILESTONE_STATUS
    assert status.status["ms_co_declaration"] == "not_occurred"
    
    # 状態を更新（可変であることを確認）
    status.status["ms_co_declaration"] = "occurred"
    assert status.status["ms_co_declaration"] == "occurred"
    print("[PASS] test_player_milestone_status_structure")


def test_player_policy_weights_structure():
    """PlayerPolicyWeights の構造検証（可変情報）"""
    weights = MOCK_POLICY_WEIGHTS
    assert weights.aggression == 7
    assert weights.trust_building == 4
    assert weights.information_reveal == 6
    assert weights.urgency == 5
    assert weights.focus_player == "Alice"
    print("[PASS] test_player_policy_weights_structure")


def test_player_policy_weights_defaults():
    """PlayerPolicyWeights のデフォルト値検証"""
    weights = PlayerPolicyWeights()
    assert weights.aggression == 5
    assert weights.trust_building == 5
    assert weights.information_reveal == 5
    assert weights.urgency == 5
    assert weights.focus_player is None
    print("[PASS] test_player_policy_weights_defaults")


def test_strategy_plan_includes_milestone_plan():
    """StrategyPlan に milestone_plan が含まれることを検証"""
    plan = MOCK_STRATEGY_PLAN
    assert plan.milestone_plan is not None
    assert len(plan.milestone_plan.milestones) == 1
    assert plan.milestone_plan.milestones[0].id == "ms_co_declaration"
    print("[PASS] test_strategy_plan_includes_milestone_plan")


def test_strategy_plan_with_default_milestone_plan():
    """StrategyPlan のデフォルト milestone_plan 検証"""
    plan = StrategyPlan(
        initial_goal="test",
        victory_condition="test",
        defeat_condition="test",
        role_behavior="test",
        co_policy="no_co"
    )
    assert plan.milestone_plan is not None
    assert isinstance(plan.milestone_plan, PlayerMilestonePlan)
    assert len(plan.milestone_plan.milestones) == 0
    print("[PASS] test_strategy_plan_with_default_milestone_plan")


if __name__ == "__main__":
    try:
        test_player_milestone_structure()
        test_player_milestone_plan_structure()
        test_player_milestone_status_structure()
        test_player_policy_weights_structure()
        test_player_policy_weights_defaults()
        test_strategy_plan_includes_milestone_plan()
        test_strategy_plan_with_default_milestone_plan()
        print("\nAll tests passed!")
    except AssertionError as e:
        print(f"Test failed: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"An error occurred: {e}")
        sys.exit(1)
