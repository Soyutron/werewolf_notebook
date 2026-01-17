
import sys
from unittest.mock import MagicMock
from src.game.player.speak_generator import SpeakGenerator
from src.core.memory.strategy import Strategy
from src.core.types import PlayerMemory, GameEvent

def test_unknown_result_prompt():
    # Setup
    generator = SpeakGenerator(llm=MagicMock())
    
    # Mock Memory
    memory = MagicMock(spec=PlayerMemory)
    memory.observed_events = []
    memory.role_beliefs = {}
    memory.history = []
    memory.self_name = "Taro"
    
    # Mock Observed
    observed = MagicMock(spec=GameEvent)
    
    # Strategy with unknown result
    strategy = Strategy(
        kind="strategy",
        co_decision="co_now",
        co_target="Kenta",
        co_result="unknown",
        action_stance="defensive",
        main_claim="Testing",
        goals=["Test"],
        approach="Test approach",
        key_points=["Test point"]
    )
    
    # Generate Prompt
    prompt = generator._build_prompt(memory=memory, observed=observed, strategy=strategy)
    
    print("--- Generated Prompt Snippet ---")
    start_idx = prompt.find("MANDATORY CO")
    end_idx = prompt.find("STRATEGY TO FOLLOW")
    print(prompt[start_idx:end_idx])
    print("--------------------------------")
    
    # Check for failure condition
    if "Result: unknown" in prompt or "結果はunknown" in prompt:
        print("FAILURE: 'unknown' found in prompt.")
        sys.exit(1)
    
    # Check for success condition
    if "Decide a result" in prompt or "結果は<DECIDE_YOURSELF>" in prompt:
        print("SUCCESS: 'unknown' handled correctly.")
    else:
        # If we haven't implemented the fix yet, this part might not match anything specific,
        # but the FAILURE condition above should trigger if the bug exists.
        print("INFO: 'unknown' not found, but explicit instruction not found either (or test logic mismatch).")

if __name__ == "__main__":
    test_unknown_result_prompt()
