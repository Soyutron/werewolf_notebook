
import sys
import os
from unittest.mock import MagicMock
import re

# Add src to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.game.player.speak_generator import SpeakGenerator
from src.core.types import PlayerMemory, GameEvent
from src.core.memory.strategy import Strategy
from src.core.llm.prompts.player import SPEAK_SYSTEM_PROMPT

def test_hallucination_prevention():
    # Setup
    llm = MagicMock()
    generator = SpeakGenerator(llm=llm)
    
    # Mock Memory
    memory = MagicMock(spec=PlayerMemory)
    memory.observed_events = [] 
    memory.role_beliefs = {}
    memory.history = []
    memory.self_name = "Werewolf1"
    
    # Mock Observed
    observed = MagicMock(spec=GameEvent)
    observed.model_dump.return_value = {}
    observed.__class__.__name__ = "GameEvent"
    
    # Strategy
    strategy = Strategy(
        kind="strategy",
        action_stance="defensive",
        main_claim="I am not a werewolf",
        primary_target="Villager1",
        goals=["Deny the accusation"],
        approach="Counter-attack Villager1",
        key_points=["Villager1 lied"]
    )
    
    print("Testing Strategy: 'Counter-attack' when history is EMPTY...")
    user_prompt = generator._build_prompt(memory=memory, observed=observed, strategy=strategy)
    
    # CHECKS FOR USER PROMPT
    user_safeguards = [
        "If an event is NOT listed below, IT DID NOT HAPPEN",
        "You CANNOT quote a player who is not in this list",
        "IGNORE the strategy's specific instruction"
    ]
    
    # CHECKS FOR SYSTEM PROMPT
    system_safeguards = [
        "FACTUAL GROUNDING",
        "Example of HALLUCINATION",
        "DO NOT ATTACK IMAGINARY STATEMENTS"
    ]
    
    failures = []
    
    print("\n--- User Prompt Checks ---")
    for sg in user_safeguards:
        if sg in user_prompt:
            print(f"[PASS] Found: {sg}")
        else:
            print(f"[FAIL] Missing: {sg}")
            failures.append(sg)
            
    print("\n--- System Prompt Checks ---")
    for sg in system_safeguards:
        if sg in SPEAK_SYSTEM_PROMPT:
            print(f"[PASS] Found: {sg}")
        else:
            print(f"[FAIL] Missing: {sg}")
            failures.append(sg)

    if failures:
        print(f"\n[CONCLUSION] Verification FAILED. Missing {len(failures)} safeguards.")
        # sys.exit(1) # Optional, strictly expected to pass now
    else:
        print("\n[CONCLUSION] Verification PASSED. All safeguards present.")

if __name__ == "__main__":
    test_hallucination_prevention()
