# tests/game/gm/test_gm_milestone_status_updater.py
import pytest
from src.game.gm.gm_milestone_status_updater import GMMilestoneStatusUpdater
from src.core.memory.gm_plan import GMMilestonePlan, GMMilestone, GMMilestoneStatus
from src.core.types.events import GameEvent

@pytest.fixture
def updater():
    return GMMilestoneStatusUpdater()

def test_initial_status(updater):
    plan = GMMilestonePlan(milestones=[
        GMMilestone(id="ms1", description="test1", trigger_condition="vote"),
        GMMilestone(id="ms2", description="test2", trigger_condition="co")
    ])
    status = updater.initialize_status(plan)
    assert status.status["ms1"] == "not_occurred"
    assert status.status["ms2"] == "not_occurred"

def test_update_status_simple(updater):
    plan = GMMilestonePlan(milestones=[
        GMMilestone(id="ms1", description="Vote started", trigger_condition="vote")
    ])
    status = GMMilestoneStatus(status={"ms1": "not_occurred"})
    
    events = [GameEvent(event_type="vote", payload={"target": "p1"})]
    new_status = updater.update(plan, status, events)
    
    assert new_status.status["ms1"] == "occurred"

def test_update_status_no_match(updater):
    plan = GMMilestonePlan(milestones=[
        GMMilestone(id="ms1", description="Counter CO", trigger_condition="counter")
    ])
    status = GMMilestoneStatus(status={"ms1": "not_occurred"})
    
    events = [GameEvent(event_type="speak", payload={"text": "hello"})]
    new_status = updater.update(plan, status, events)
    
    assert new_status.status["ms1"] == "not_occurred"

def test_update_status_counter_co(updater):
    plan = GMMilestonePlan(milestones=[
        GMMilestone(id="ms1", description="Counter CO", trigger_condition="対抗")
    ])
    status = GMMilestoneStatus(status={"ms1": "not_occurred"})
    
    # "co" event but with "対抗" in payload or implicit context if implemented
    # Here we test trigger matching logic for "counter" type or keyword
    events = [GameEvent(event_type="counter", payload={"player": "p2"})]
    new_status = updater.update(plan, status, events)
    
    assert new_status.status["ms1"] == "occurred"

def test_update_status_already_occurred(updater):
    plan = GMMilestonePlan(milestones=[
        GMMilestone(id="ms1", description="Vote", trigger_condition="vote")
    ])
    status = GMMilestoneStatus(status={"ms1": "occurred"})
    
    events = [GameEvent(event_type="vote", payload={})]
    new_status = updater.update(plan, status, events)
    
    assert new_status.status["ms1"] == "occurred" # Should remain occurred

def test_text_match_fallback(updater):
    plan = GMMilestonePlan(milestones=[
        GMMilestone(id="ms1", description="Suspicious", trigger_condition="怪しい")
    ])
    status = GMMilestoneStatus(status={"ms1": "not_occurred"})
    
    events = [GameEvent(event_type="speak", payload={"text": "あいつは怪しいな"})]
    new_status = updater.update(plan, status, events)
    
    assert new_status.status["ms1"] == "occurred"
