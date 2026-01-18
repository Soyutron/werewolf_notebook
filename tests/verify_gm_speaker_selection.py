import sys
import os
from unittest.mock import MagicMock

# Add src to path
sys.path.append(os.path.join(os.path.dirname(__file__), "../src"))

from game.gm.gm_comment_generator import GMCommentGenerator
from core.types import GameEvent

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

if __name__ == "__main__":
    test_prevent_consecutive_speaker()
