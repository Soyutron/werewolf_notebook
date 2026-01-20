import sys
from unittest.mock import MagicMock
from src.core.types.phases import GameDefinition, WorldState
from src.core.memory.gm_plan import GMProgressionPlan, GMStrategyPlan, GMMilestonePlan, GMMilestone, GMMilestoneStatus, GMPolicyWeights
from src.game.gm.gm_plan_generator import GMPlanGenerator
from src.core.llm.client import LLMClient

# Mock Data
MOCK_STRATEGY = GMStrategyPlan(
    main_objective="Test Objective",
    key_scenarios=["Scenario 1"],
    discussion_points=["Point 1"]
)
MOCK_MILESTONE_PLAN = GMMilestonePlan(
    milestones=[GMMilestone(id="test_ms", description="Test MS", trigger_condition="Condition")]
)
MOCK_MILESTONE_STATUS = GMMilestoneStatus(status={"test_ms": "not_occurred"})
MOCK_POLICY_WEIGHTS = GMPolicyWeights(intervention_level=3, pacing_speed=3, humor_level=3, focus_player="Alice")

MOCK_FULL_PLAN = GMProgressionPlan(
    strategy_plan=MOCK_STRATEGY,
    milestone_plan=MOCK_MILESTONE_PLAN,
    milestone_status=MOCK_MILESTONE_STATUS,
    policy_weights=MOCK_POLICY_WEIGHTS
)

def test_gm_plan_structure():
    """Verify that GMProgressionPlan structure is valid and can be instantiated."""
    plan = MOCK_FULL_PLAN
    assert plan.strategy_plan.main_objective == "Test Objective"
    assert plan.policy_weights.intervention_level == 3
    
    summary = plan.get_summary_markdown()
    assert "# GM Strategy: Test Objective" in summary
    assert "- [not_occurred] Test MS" in summary
    assert "- Intervention: 3" in summary
    print("[PASS] test_gm_plan_structure")

def test_gm_plan_generator_returns_object():
    """Verify GMPlanGenerator returns a GMProgressionPlan object."""
    mock_llm = MagicMock(spec=LLMClient)
    mock_llm.generate.return_value = MOCK_FULL_PLAN
    
    generator = GMPlanGenerator(mock_llm)
    from src.core.types.roles import RoleDefinition
    
    world_state = WorldState(phase="night", players=["Alice", "Bob"], public_events=[], pending_events=[])
    
    roles = {
        "werewolf": RoleDefinition(name="werewolf", day_side="werewolf", win_side="werewolf"),
        "villager": RoleDefinition(name="villager", day_side="village", win_side="village")
    }
    game_def = GameDefinition(
        roles=roles,
        role_distribution=["werewolf", "villager"],
        phases=["night", "day", "vote"]
    )
    
    result = generator.generate(world_state, game_def)
    
    assert isinstance(result, GMProgressionPlan)
    assert result.strategy_plan.main_objective == "Test Objective"
    
    # Check if LLM was called with correct system prompt (indirectly checking prompt import)
    # We can check args passed to generate
    mock_llm.generate.assert_called_once()
    kwargs = mock_llm.generate.call_args.kwargs
    assert "strategy_plan" in kwargs['system'] # JSON format hint in system prompt
    assert "GM_PLAN_SYSTEM_PROMPT" not in kwargs['system'] # ensure variable was resolved (if we check content)
    print("[PASS] test_gm_plan_generator_returns_object")

from src.game.gm.gm_comment_generator import GMCommentGenerator
from src.core.types import GameEvent

def test_gm_comment_generator_uses_plan():
    """Verify GMCommentGenerator utilizes the plan in prompt construction."""
    mock_llm = MagicMock()
    generator = GMCommentGenerator(mock_llm)
    
    players = ["Alice", "Bob"]
    speak_counts = {"Alice": 0, "Bob": 0}
    
    # Verify _build_prompt includes policy info
    prompt = generator._build_prompt(
        players=players,
        next_speaker="Alice",
        selection_reason="round_robin",
        is_opening=False,
        speak_counts=speak_counts,
        last_speaker=None,
        progression_plan=MOCK_FULL_PLAN
    )
    
    assert "進行計画" in prompt
    assert "Test Objective" in prompt # From summary
    assert "現在の行動指針" in prompt
    assert "介入レベル: 3" in prompt
    print("[PASS] test_gm_comment_generator_uses_plan")

if __name__ == "__main__":
    try:
        test_gm_plan_structure()
        test_gm_plan_generator_returns_object()
        test_gm_comment_generator_uses_plan()
        print("All tests passed!")
    except AssertionError as e:
        print(f"Test failed: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"An error occurred: {e}")
        sys.exit(1)
