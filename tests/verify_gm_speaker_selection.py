import sys
import os
from unittest.mock import MagicMock

# Add src to path
# Set dummy API key to prevent ValueError during import of global instances
os.environ["GOOGLE_API_KEY"] = "dummy"

# Add project root to path (parent of tests)
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from src.core.types import GameEvent
from src.core.memory.gm_comment import GMComment

# Mock src.config.llm to prevent circular imports during test
import sys
from unittest.mock import MagicMock
sys.modules["src.config.llm"] = MagicMock()

from src.game.gm.gm_comment_generator import GMCommentGenerator

def test_prevent_consecutive_speaker():
    """
    Test that the GM does not select the same speaker consecutively.
    This is verified by checking the 'Candidate Speakers' list passed to the LLM prompt.
    """
    mock_llm = MagicMock()
    # Mock response is not critical for this test, but we need something valid-ish
    mock_llm.generate.return_value = None 

    generator = GMCommentGenerator(llm=mock_llm)

    players = ["PlayerA", "PlayerB", "PlayerC"]
    
    # History where PlayerA just spoke
    public_events = [
        GameEvent(event_type="speak", payload={"player": "PlayerB", "text": "Hello"}),
        GameEvent(event_type="speak", payload={"player": "PlayerA", "text": "I am Player A"}),
    ]

    generator.generate(public_events=public_events, players=players)

    # Inspect the call args to see if PlayerA was excluded from candidates
    # We look at the 'prompt' argument passed to llm.generate
    call_args = mock_llm.generate.call_args
    if not call_args:
        print("FAIL: LLM was not called")
        return

    kwargs = call_args.kwargs
    prompt = kwargs.get("prompt", "")
    
    print("--- Prompt sent to LLM ---")
    print(prompt)
    print("------------------------")

    if "Candidate Speakers" not in prompt:
         print("FAIL: 'Candidate Speakers' section missing in prompt")
         return

    if "- PlayerA" in prompt.split("Candidate Speakers")[1]:
        print("FAIL: PlayerA (last speaker) was found in Candidate Speakers")
    else:
        print("SUCCESS: PlayerA correctly excluded from Candidate Speakers")

def test_force_correction_on_bad_LLM_selection():
    """
    Test that if LLM ignores the prompt and selects the last speaker,
    the python code overrides it with a valid candidate.
    """
    mock_llm = MagicMock()
    # Mock LLM returns PlayerA (who is the last speaker)
    mock_llm.generate.return_value = GMComment(speaker="PlayerA", text="Invalid selection")

    generator = GMCommentGenerator(llm=mock_llm)

    players = ["PlayerA", "PlayerB", "PlayerC"]
    
    # PlayerA spoke last
    public_events = [
        GameEvent(event_type="speak", payload={"player": "PlayerB", "text": "Hello"}),
        GameEvent(event_type="speak", payload={"player": "PlayerA", "text": "I am Player A"}),
    ]

    response = generator.generate(public_events=public_events, players=players)

    print("\n--- Testing Logic Override ---")
    print(f"LLM returned: PlayerA (Invalid)")
    print(f"Generator returned: {response.speaker}")

    if response.speaker == "PlayerA":
        print("FAIL: Generator accepted invalid speaker (PlayerA)")
    elif response.speaker in ["PlayerB", "PlayerC"]:
        print(f"SUCCESS: Generator overrided invalid speaker with {response.speaker}")
    else:
        print(f"FAIL: Generator selected unknown speaker {response.speaker}")


if __name__ == "__main__":
    test_prevent_consecutive_speaker()
    test_force_correction_on_bad_LLM_selection()
