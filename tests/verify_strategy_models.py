import sys
import os

# Add src to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from src.core.memory.strategy import StrategyPlan

def test_strategy_plan_model():
    print("Testing StrategyPlan model instantiation...")
    try:
        plan = StrategyPlan(
            initial_goal="My Goal",
            victory_condition="Win condition",
            defeat_condition="Defeat condition",
            role_behavior="Behavior",
            must_not_do=["Do not panic", "Do not claim GM"],
            co_policy="no_co",
            intended_co_role=None
        )
        print("Successfully instantiated StrategyPlan:")
        print(plan.model_dump_json(indent=2))
        return True
    except Exception as e:
        print(f"Failed to instantiate StrategyPlan: {e}")
        return False

if __name__ == "__main__":
    if test_strategy_plan_model():
        print("Model verification PASSED")
        sys.exit(0)
    else:
        print("Model verification FAILED")
        sys.exit(1)
