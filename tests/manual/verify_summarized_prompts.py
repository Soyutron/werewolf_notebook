
import sys
import os

# Add src to path
sys.path.append(os.path.join(os.path.dirname(__file__), "../../"))

from src.game.player.speak_generator import SpeakGenerator
from src.game.gm.gm_comment_generator import GMCommentGenerator
from src.game.player.strategy_generator import StrategyGenerator
from src.core.types import PlayerMemory, GameEvent, PlayerRequest
from src.core.types.player import RoleProb
from src.core.memory.strategy import StrategyPlan
from pydantic import BaseModel

class MockLLM:
    def __init__(self):
        self.last_prompt = None
        self.last_system = None

    def generate(self, system, prompt):
        self.last_prompt = prompt
        self.last_system = system
        return "MOCKED_RESPONSE"

def test_speak_generator_prompt():
    print("Testing SpeakGenerator prompt...")
    generator = SpeakGenerator(llm=MockLLM())
    
    memory = PlayerMemory(
        self_name="Player1",
        self_role="villager",
        players=["Player1", "Player2"],
        log_summary="[Summary] Player1 COs Villager.",
        role_beliefs={"Player2": RoleProb(probs={"villager": 1.0})}, # Mock or simplified
        observed_events=[
            GameEvent(event_type="speak", payload={"player": "Player1", "text": "I am a villager."}),
            GameEvent(event_type="speak", payload={"player": "Player2", "text": "I trust Player1."}),
        ]
    )
    observed = PlayerRequest(request_type="speak", payload={})
    
    prompt = generator._build_prompt(memory=memory, observed=observed)
    
    # Verification
    if "[Summary] Player1 COs Villager." not in prompt:
        print("FAILED: Summary not found in prompt.")
    else:
        print("PASSED: Summary found.")
        
    if "I trust Player1." in prompt:
        print("FAILED: Raw event text (Player2's speech) found in prompt (should be removed).")
    else:
        print("PASSED: Raw event text not found.")

def test_gm_generator_prompt():
    print("\nTesting GMCommentGenerator prompt...")
    generator = GMCommentGenerator(llm=MockLLM())
    
    players = ["Player1", "Player2"]
    public_events = [
         GameEvent(event_type="speak", payload={"player": "Player1", "text": "GM Check 1"}),
         GameEvent(event_type="speak", payload={"player": "Player2", "text": "GM Check 2"}),
    ]
    
    
    # Run generate() to test full flow and check for NameError
    try:
        generator.generate(
            public_events=public_events,
            players=players,
            log_summary="[Summary] Game is ongoing."
        )
        print("PASSED: generator.generate() ran without NameError.")
    except Exception as e:
        print(f"FAILED: generator.generate() raised {type(e).__name__}: {e}")
        return

    prompt = generator.llm.last_prompt
    
    # Verification
    if prompt and "[Summary] Game is ongoing." not in prompt:
        print("FAILED: Summary not found in prompt.")
    else:
        print("PASSED: Summary found.")

    if prompt and "GM Check 1" in prompt:
         print("FAILED: Raw event text found in prompt.")
    else:
         print("PASSED: Raw event text not found.")

def test_strategy_generator_prompt():
    print("\nTesting StrategyGenerator prompt...")
    generator = StrategyGenerator(llm=MockLLM())
    
    memory = PlayerMemory(
        self_name="Player1",
        self_role="villager",
        players=["Player1", "Player2"],
        log_summary="[Summary] Strategy Context.",
        role_beliefs={"Player2": RoleProb(probs={"villager": 1.0})},
        observed_events=[
            GameEvent(event_type="speak", payload={"player": "Player1", "text": "Strategy Raw 1"}),
        ]
    )
    
    prompt = generator._build_guideline_prompt(memory=memory, plan=None)
    
    # Verification
    if "[Summary] Strategy Context." not in prompt:
        print("FAILED: Summary not found in prompt.")
    else:
        print("PASSED: Summary found.")
        
    if "Strategy Raw 1" in prompt:
        print("FAILED: Raw event text found in prompt.")
    else:
        print("PASSED: Raw event text not found.")

if __name__ == "__main__":
    test_speak_generator_prompt()
    test_gm_generator_prompt()
    test_strategy_generator_prompt()
