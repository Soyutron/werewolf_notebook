import sys
import os

# Add src to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

try:
    from src.core.llm.prompts import strategy
    print("Successfully imported src.core.llm.prompts.strategy")
    
    # Check if key variables exist
    print(f"COMMON_STRATEGY_OUTPUT_FORMAT length: {len(strategy.COMMON_STRATEGY_OUTPUT_FORMAT)}")
    print(f"SEER_STRATEGY_SYSTEM_PROMPT length: {len(strategy.SEER_STRATEGY_SYSTEM_PROMPT)}")
    print("Verification passed!")
except Exception as e:
    print(f"Verification FAILED: {e}")
    sys.exit(1)
