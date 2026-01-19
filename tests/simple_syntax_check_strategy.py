import sys
import os

# Add src to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

try:
    from src.core.llm.prompts import strategy
    print("Successfully imported src.core.llm.prompts.strategy")
    
    # Check if key variables exist
    print(f"COMMON_STRATEGY_OUTPUT_FORMAT length: {len(strategy.COMMON_STRATEGY_OUTPUT_FORMAT)}")
    
    # from src.core.llm.prompts import initial_strategy_system_prompt_source_check = strategy.INITIAL_STRATEGY_SYSTEM_PROMPT
    # The above line is intentionally removed as it would be invalid.

    # Correct check:
    from src.core.llm.prompts import strategy_plan
    print(f"INITIAL_STRATEGY_SYSTEM_PROMPT length: {len(strategy_plan.INITIAL_STRATEGY_SYSTEM_PROMPT)}")
    
    print(f"SEER_STRATEGY_SYSTEM_PROMPT length: {len(strategy.SEER_STRATEGY_SYSTEM_PROMPT)}")
    print("Verification passed!")
except Exception as e:
    print(f"Verification FAILED: {e}")
    sys.exit(1)
