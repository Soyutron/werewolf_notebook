import sys
import os

# プロジェクトルートをパスに追加
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../../")))

from unittest.mock import MagicMock, patch
from src.core.types import GMGraphState, GMInternalState, WorldState, GameDecision
from src.graphs.gm.node.gm_plan import gm_plan_node
from src.graphs.gm.gm_graph import build_gm_graph


from src.core.memory.gm_plan import GMProgressionPlan

from src.core.types.phases import GameDefinition

def test_gm_plan_node():
    print("=== Testing gm_plan_node ===")
    
    # Mock
    mock_llm = MagicMock()
    mock_llm.generate.return_value = GMProgressionPlan(content="- Plan Item 1\n- Plan Item 2")
    
    # State setup
    internal = GMInternalState(
        night_pending=[],
        vote_pending=[],
        progression_plan=""
    )
    world_state = WorldState(
        phase="night",
        players=["A", "B"],
        public_events=[]
    )
    game_def = GameDefinition(
        roles={
            "villager": {"name": "villager", "day_side": "village", "win_side": "village"},
            "werewolf": {"name": "werewolf", "day_side": "werewolf", "win_side": "werewolf"}
        },
        role_distribution=["villager", "werewolf"],
        phases=["night", "day", "vote"]
    )

    state: GMGraphState = {
        "internal": internal,
        "world_state": world_state,
        "decision": GameDecision(),
        "game_def": game_def
    }
    
    # Patch create_gm_plan_llm
    with patch("src.graphs.gm.node.gm_plan.create_gm_plan_llm", return_value=mock_llm):
        # 1. First run: Should generate plan
        new_state = gm_plan_node(state)
        # Verify internal state updated
        plan = new_state["internal"].progression_plan
        print(f"Generated Plan: {plan}")
        assert plan == "- Plan Item 1\n- Plan Item 2"
        # Verify LLM called
        assert mock_llm.generate.called
        
        # 2. Second run: Should NOT generate plan (Idempotency)
        mock_llm.generate.reset_mock()
        new_state_2 = gm_plan_node(new_state)
        assert new_state_2["internal"].progression_plan == plan
        assert not mock_llm.generate.called
        print("Idempotency check passed")


def test_gm_graph_structure():
    print("\n=== Testing GMGraph Structure ===")
    graph = build_gm_graph()
    # Check if 'night' node exists and edges are correct
    # Note: CompiledGraph internal structure is complex, manual inspection of nodes is hard via public API.
    # We can invoke it essentially using a dummy runner if we wanted, but basic build check is good enough.
    print("GMGraph built successfully")
    
    # Validate specific edges if we can assume networkx compatibility or similar, 
    # but for now just building it proves syntactic correctness.


if __name__ == "__main__":
    try:
        test_gm_plan_node()
        test_gm_graph_structure()
        print("\nAll tests passed!")
    except Exception as e:
        print(f"\nTEST FAILED: {e}")
        import traceback
        traceback.print_exc()
        exit(1)
