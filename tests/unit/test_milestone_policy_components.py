"""
Unit tests for Player Strategy Structure - New Components.

Tests verify the new milestone/policy weight components:
- MilestoneStatusUpdater
- PolicyWeightsCalculator

These tests are isolated and don't require LLM API keys.
Uses direct module loading to avoid __init__.py cascade.
"""
import sys
import os
import importlib.util

# Add project root to path
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "../.."))
sys.path.insert(0, project_root)

# Load pydantic first (required dependency)
from pydantic import BaseModel, Field
from typing import List, Optional, Literal, Dict


def load_module_direct(name, relative_path):
    """Load a module directly from file path, avoiding __init__.py."""
    full_path = os.path.join(project_root, relative_path)
    spec = importlib.util.spec_from_file_location(name, full_path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


# Load strategy module directly
strategy_module = load_module_direct(
    "src.core.memory.strategy",
    "src/core/memory/strategy.py"
)

PlayerMilestone = strategy_module.PlayerMilestone
PlayerMilestonePlan = strategy_module.PlayerMilestonePlan
PlayerMilestoneStatus = strategy_module.PlayerMilestoneStatus
PlayerPolicyWeights = strategy_module.PlayerPolicyWeights
StrategyPlan = strategy_module.StrategyPlan


# Mock GameEvent for testing (avoid importing from src.core.types.game)
class MockGameEvent(BaseModel):
    """Mock GameEvent for testing."""
    event_type: str
    payload: dict = {}


# Patch the game module to use MockGameEvent
class MockGameModule:
    GameEvent = MockGameEvent

sys.modules["src.core.types.game"] = MockGameModule()

# Now load the updater and calculator
updater_module = load_module_direct(
    "src.game.player.milestone_status_updater",
    "src/game/player/milestone_status_updater.py"
)
MilestoneStatusUpdater = updater_module.MilestoneStatusUpdater

calculator_module = load_module_direct(
    "src.game.player.policy_weights_calculator",
    "src/game/player/policy_weights_calculator.py"
)
PolicyWeightsCalculator = calculator_module.PolicyWeightsCalculator


# ===========================================
# Mock Data
# ===========================================
MOCK_MILESTONES = [
    PlayerMilestone(
        id="ms_co_declaration",
        description="誰かが役職COする",
        trigger_condition="COイベントが発生",
        importance="high"
    ),
    PlayerMilestone(
        id="ms_counter_co",
        description="対抗COが発生する",
        trigger_condition="対抗COイベント",
        importance="high"
    ),
    PlayerMilestone(
        id="ms_discussion_active",
        description="活発な議論が行われる",
        trigger_condition="speakイベントが複数発生",
        importance="medium"
    ),
]

MOCK_MILESTONE_PLAN = PlayerMilestonePlan(milestones=MOCK_MILESTONES)

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
# MilestoneStatusUpdater Tests
# ===========================================
def test_milestone_status_updater_initialization():
    """MilestoneStatusUpdater の初期化テスト"""
    updater = MilestoneStatusUpdater()
    status = updater.initialize_status(MOCK_MILESTONE_PLAN)
    
    assert len(status.status) == 3
    assert status.status["ms_co_declaration"] == "not_occurred"
    assert status.status["ms_counter_co"] == "not_occurred"
    assert status.status["ms_discussion_active"] == "not_occurred"
    print("[PASS] test_milestone_status_updater_initialization")


def test_milestone_status_updater_no_events():
    """イベントなしの場合、状態が変わらない"""
    updater = MilestoneStatusUpdater()
    initial_status = PlayerMilestoneStatus(status={
        "ms_co_declaration": "not_occurred",
        "ms_counter_co": "not_occurred",
    })
    
    updated = updater.update(MOCK_MILESTONE_PLAN, initial_status, [])
    
    assert updated.status["ms_co_declaration"] == "not_occurred"
    assert updated.status["ms_counter_co"] == "not_occurred"
    print("[PASS] test_milestone_status_updater_no_events")


def test_milestone_status_updater_with_matching_event():
    """マッチするイベントで状態が更新される"""
    updater = MilestoneStatusUpdater()
    initial_status = PlayerMilestoneStatus(status={
        "ms_co_declaration": "not_occurred",
        "ms_counter_co": "not_occurred",
        "ms_discussion_active": "not_occurred",
    })
    
    # COイベントを発生させる
    co_event = MockGameEvent(
        event_type="co",
        payload={"player": "Alice", "role": "seer"}
    )
    
    updated = updater.update(MOCK_MILESTONE_PLAN, initial_status, [co_event])
    
    # high importance なので strong になる
    assert updated.status["ms_co_declaration"] == "strong"
    # 他は変わらない
    assert updated.status["ms_counter_co"] == "not_occurred"
    print("[PASS] test_milestone_status_updater_with_matching_event")


# ===========================================
# PolicyWeightsCalculator Tests
# ===========================================
def test_policy_weights_calculator_defaults():
    """デフォルト値の確認"""
    calculator = PolicyWeightsCalculator()
    weights = calculator.get_default_weights()
    
    assert weights.aggression == 5
    assert weights.trust_building == 5
    assert weights.information_reveal == 5
    assert weights.urgency == 5
    assert weights.focus_player is None
    print("[PASS] test_policy_weights_calculator_defaults")


def test_policy_weights_calculator_no_milestones():
    """マイルストーンなしの場合のデフォルト値"""
    calculator = PolicyWeightsCalculator()
    empty_plan = PlayerMilestonePlan(milestones=[])
    empty_status = PlayerMilestoneStatus(status={})
    
    weights = calculator.calculate(empty_plan, empty_status)
    
    assert weights.aggression == 5
    assert weights.trust_building == 5
    print("[PASS] test_policy_weights_calculator_no_milestones")


def test_policy_weights_calculator_with_occurred_milestones():
    """マイルストーン発生時の重み調整"""
    calculator = PolicyWeightsCalculator()
    
    # high importance のマイルストーンが発生
    status = PlayerMilestoneStatus(status={
        "ms_co_declaration": "strong",  # high importance, strong
        "ms_counter_co": "not_occurred",
        "ms_discussion_active": "not_occurred",
    })
    
    weights = calculator.calculate(MOCK_MILESTONE_PLAN, status, MOCK_STRATEGY_PLAN)
    
    # strong + high importance で urgency と aggression が上がる
    assert weights.urgency > 5
    assert weights.aggression > 5
    # immediate CO policy なので information_reveal も上がる
    assert weights.information_reveal > 5
    print("[PASS] test_policy_weights_calculator_with_occurred_milestones")


def test_policy_weights_calculator_values_clamped():
    """重み値が1-10の範囲に収まることを確認"""
    calculator = PolicyWeightsCalculator()
    
    # 全ての high importance マイルストーンが strong で発生
    status = PlayerMilestoneStatus(status={
        "ms_co_declaration": "strong",
        "ms_counter_co": "strong",
        "ms_discussion_active": "strong",
    })
    
    weights = calculator.calculate(MOCK_MILESTONE_PLAN, status, MOCK_STRATEGY_PLAN)
    
    assert 1 <= weights.aggression <= 10
    assert 1 <= weights.trust_building <= 10
    assert 1 <= weights.information_reveal <= 10
    assert 1 <= weights.urgency <= 10
    print("[PASS] test_policy_weights_calculator_values_clamped")


# ===========================================
# Main
# ===========================================
if __name__ == "__main__":
    try:
        # MilestoneStatusUpdater tests
        test_milestone_status_updater_initialization()
        test_milestone_status_updater_no_events()
        test_milestone_status_updater_with_matching_event()
        
        # PolicyWeightsCalculator tests
        test_policy_weights_calculator_defaults()
        test_policy_weights_calculator_no_milestones()
        test_policy_weights_calculator_with_occurred_milestones()
        test_policy_weights_calculator_values_clamped()
        
        print("\n" + "=" * 50)
        print("All tests passed!")
        print("=" * 50)
    except AssertionError as e:
        print(f"Test failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
    except Exception as e:
        print(f"An error occurred: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
