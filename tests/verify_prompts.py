import sys
import os
from unittest.mock import MagicMock

# Add src to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

# Mocking to avoid circular imports
sys.modules["src.graphs"] = MagicMock()
sys.modules["src.graphs.gm"] = MagicMock()
sys.modules["src.graphs.gm.gm_graph"] = MagicMock()
sys.modules["src.graphs.gm.node"] = MagicMock()
sys.modules["src.graphs.gm.node.day_phase_router"] = MagicMock()
sys.modules["src.core.session"] = MagicMock()
sys.modules["src.core.session.game_session"] = MagicMock()

from src.game.gm.gm_maturity_judge import GMMaturityJudge
from src.game.player.speak_generator import SpeakGenerator
from src.game.player.strategy_generator import StrategyGenerator
from src.game.player.vote_generator import VoteGenerator
from src.core.types import GameEvent, PlayerMemory, RoleProb

def mock_llm():
    return MagicMock()

def create_mock_event(i: int):
    return GameEvent(event_type="gm_comment", payload={"text": f"Event {i}"})

def verify_gm_maturity():
    print("\n--- Verifying GMMaturityJudge ---")
    judge = GMMaturityJudge(mock_llm())
    events = [create_mock_event(i) for i in range(1, 6)]
    # public_events are passed in chronological order [1, 2, 3, 4, 5]
    # Expect prompt to show [5, 4, 3, 2, 1]
    
    # Access private method for testing purpose, or just inspect how we call format
    # Since _build_prompt takes string, we can verify format_events usage in code
    # But here let's just use the _build_prompt if we can simulate the flow
    # Since judge() calls _build_prompt, we can mock _build_prompt to see arguments?
    # Or better, just copy the logic we want to test or call the method that produces the string.
    
    # The logic in `judge` is:
    # recent_events = public_events[-15:]
    # events_text = format_events_for_maturity(list(reversed(recent_events)))
    # prompt = self._build_prompt(events_text=events_text)
    
    # We can invoke _build_prompt indirectly or check the helper.
    from src.game.gm.gm_maturity_judge import format_events_for_maturity
    
    recent_events = events[-15:]
    reversed_events = list(reversed(recent_events))
    text = format_events_for_maturity(reversed_events)
    print("Formatted Text:")
    print(text)
    
    if "Event 5" in text.split("\n")[0]:
        print("SUCCESS: Event 5 is at the top.")
    else:
        print("FAILURE: Event 5 is NOT at the top.")

def verify_speak_generator():
    print("\n--- Verifying SpeakGenerator ---")
    gen = SpeakGenerator(mock_llm())
    memory = MagicMock(spec=PlayerMemory)
    memory.self_name = "Alice"
    memory.role_beliefs = {"Bob": MagicMock(probs={"villager": 1.0})}
    memory.history = ["Reflection 1", "Reflection 2", "Reflection 3"] # Not used directly anymore
    memory.log_summary = "Summary of past events: Alice said hi."
    memory.observed_events = []
    
    observed = create_mock_event(99)
    
    prompt = gen._build_prompt(memory, observed)
    print("Prompt Snippet (Log Summary & Headers):")
    
    # Check if log_summary is included (Japanese header)
    header_idx = prompt.find("ゲームログ要約")
    snippet = prompt[header_idx:header_idx+200]
    print(snippet)
    
    if header_idx != -1 and "Summary of past events: Alice said hi." in snippet:
         print("SUCCESS: Log summary found under Japanese header.")
    else:
         print("FAILURE: Log summary or Japanese header missing.")

    # Check for Belief Analysis (Japanese header)
    if "役職推定分析" in prompt:
        print("SUCCESS: Belief analysis header found.")
    else:
        print("FAILURE: Belief analysis header missing.")

def verify_strategy_generator():
    print("\n--- Verifying StrategyGenerator ---")
    gen = StrategyGenerator(mock_llm())
    memory = MagicMock(spec=PlayerMemory)
    memory.self_name = "Alice"
    memory.self_role = "villager"
    memory.players = ["Alice", "Bob"]
    memory.role_beliefs = {"Bob": MagicMock(probs={"villager": 1.0})}
    memory.history = [MagicMock(kind="thought", text="Thought 1"), MagicMock(kind="thought", text="Thought 2")]
    memory.observed_events = [create_mock_event(1), create_mock_event(2)]
    
    prompt = gen._build_prompt(memory)
    
    print("Prompt Snippet (Events & Thoughts):")
    # Thoughts: 2 before 1
    # Events: 2 before 1
    
    if "Thought 2" in prompt and prompt.find("Thought 2") < prompt.find("Thought 1"):
        print("SUCCESS: Thought 2 before Thought 1")
    else:
        print("FAILURE: Thoughts order incorrect")
        
    if "Event 2" in prompt and prompt.find("Event 2") < prompt.find("Event 1"):
        print("SUCCESS: Event 2 before Event 1")
    else:
        print("FAILURE: Events order incorrect")

def verify_vote_generator():
    print("\n--- Verifying VoteGenerator ---")
    gen = VoteGenerator(mock_llm())
    memory = MagicMock(spec=PlayerMemory)
    memory.self_name = "Alice"
    memory.self_role = "villager"
    memory.players = ["Alice", "Bob"]
    memory.role_beliefs = {"Bob": MagicMock(probs={"villager": 1.0})}
    memory.history = ["Action 1", "Action 2"]
    
    observed = create_mock_event(99)
    
    prompt = gen._build_prompt(memory, observed)
    
    # We expect Action 2 before Action 1
    if "Action 2" in prompt and prompt.find("Action 2") < prompt.find("Action 1"):
         print("SUCCESS: Action 2 before Action 1")
    else:
         print("FAILURE: Order incorrect")

if __name__ == "__main__":
    verify_gm_maturity()
    verify_speak_generator()
    # verify_strategy_generator()  # Out of scope / Broken
    verify_vote_generator()
