import sys
import os
from unittest.mock import MagicMock

# Add src to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.game.player.speak_generator import SpeakGenerator
from src.core.types import PlayerMemory, GameEvent
from src.core.memory.strategy import Strategy

def test_warning_insertion():
    # Setup
    llm = MagicMock()
    generator = SpeakGenerator(llm=llm)
    
    # Mock Memory
    memory = MagicMock(spec=PlayerMemory)
    memory.observed_events = [] # Empty list = No one spoke
    memory.role_beliefs = {}
    memory.history = []
    memory.self_name = "Werewolf1"
    
    # Mock Observed
    observed = MagicMock(spec=GameEvent)
    observed.model_dump.return_value = {}
    observed.__class__.__name__ = "GameEvent"
    
    # Mock Strategy targeting "Villager1" who hasn't spoken
    strategy = Strategy(
        kind="strategy",
        action_stance="aggressive",
        main_claim="Villager1 is suspicious",
        primary_target="Villager1",
        goals=["Attack Villager1"],
        approach="Find contradiction in Villager1's speech",
        key_points=["Contradiction"]
    )
    
    # Run _build_prompt
    print("Testing Case 1: Target has NOT spoken...")
    prompt = generator._build_prompt(memory=memory, observed=observed, strategy=strategy)
    
    # Verify warning exists
    warning_snip = "!!! WARNING: TARGET 'Villager1' HAS NOT SPOKEN !!!"
    
    if warning_snip in prompt:
        print("[PASS] Warning found in prompt.")
        print("--- Snippet ---")
        start = prompt.find(warning_snip)
        print(prompt[start:start+200].replace('\n', ' ') + "...")
        print("---------------")
    else:
        print("[FAIL] Warning NOT found in prompt.")
        print("--- Full Prompt ---")
        print(prompt)
        print("-------------------")
        sys.exit(1)

    # Test Case 2: Target HAS spoken
    print("\nTesting Case 2: Target HAS spoken...")
    
    # Create a real GameEvent instance or mock with payload works too
    # Using MagicMock for GameEvent to match logic
    event = MagicMock(spec=GameEvent)
    event.event_type = "speak"
    event.payload = {"player": "Villager1", "text": "I am Villager."}
    
    memory.observed_events = [event]
    
    prompt2 = generator._build_prompt(memory=memory, observed=observed, strategy=strategy)
    
    if warning_snip in prompt2:
        print("[FAIL] Warning found BUT target has spoken.")
        sys.exit(1)
    else:
        print("[PASS] Warning correctly omitted when target spoke.")

if __name__ == "__main__":
    test_warning_insertion()
