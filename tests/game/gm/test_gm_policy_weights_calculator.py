# tests/game/gm/test_gm_policy_weights_calculator.py
import pytest
from src.game.gm.gm_policy_weights_calculator import GMPolicyWeightsCalculator
from src.core.memory.gm_plan import GMMilestonePlan, GMMilestone, GMMilestoneStatus, GMStrategyPlan

@pytest.fixture
def calculator():
    return GMPolicyWeightsCalculator()

def test_default_weights(calculator):
    weights = calculator.get_default_weights()
    assert weights.intervention_level == 3
    assert weights.pacing_speed == 3

def test_calculate_weights_no_progress(calculator):
    plan = GMMilestonePlan(milestones=[
        GMMilestone(id="ms1", description="m1", trigger_condition="t1"),
        GMMilestone(id="ms2", description="m2", trigger_condition="t2")
    ])
    status = GMMilestoneStatus(status={"ms1": "not_occurred", "ms2": "not_occurred"})
    
    weights = calculator.calculate(plan, status)
    assert weights.pacing_speed == 3 # Default

def test_calculate_weights_high_progress(calculator):
    plan = GMMilestonePlan(milestones=[
        GMMilestone(id="ms1", description="m1", trigger_condition="t1"),
        GMMilestone(id="ms2", description="m2", trigger_condition="t2")
    ])
    status = GMMilestoneStatus(status={"ms1": "occurred", "ms2": "occurred"})
    
    weights = calculator.calculate(plan, status)
    # 100% progress -> pacing should increase
    assert weights.pacing_speed >= 4
