import sys
import os

# Add src to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from src.core.memory.strategy import StrategyPlan, Strategy

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

def test_strategy_model():
    print("Testing Strategy model instantiation...")
    try:
        strategy = Strategy(
            co_decision="no_co",
            target_player="PlayerA",
            value_focus="logic",
            aggression_level=5,
            doubt_level=3,
            action_type="question",
            style_instruction="Calmly ask about their vote"
        )
        print("Successfully instantiated Strategy:")
        print(strategy.model_dump_json(indent=2))
        return True
    except Exception as e:
        print(f"Failed to instantiate Strategy: {e}")
        return False

if __name__ == "__main__":
    plan_ok = test_strategy_plan_model()
    strategy_ok = test_strategy_model()
    
    if plan_ok and strategy_ok:
        print("Model verification PASSED")
        sys.exit(0)
    else:
        print("Model verification FAILED")
        sys.exit(1)
