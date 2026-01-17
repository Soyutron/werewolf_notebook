import sys
import os
from unittest.mock import MagicMock

# Add project root
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

# PRE-MOCK src.config.llm
mock_config_llm = MagicMock()
sys.modules["src.config.llm"] = mock_config_llm
mock_llm_client = MagicMock()
mock_config_llm.create_speak_reviewer_llm.return_value = mock_llm_client
mock_config_llm.create_speak_refiner_llm.return_value = mock_llm_client

# Import classes
from src.game.player.speak_reviewer import SpeakReviewer
from src.game.player.speak_refiner import SpeakRefiner
from src.core.memory.speak import Speak
from src.core.memory.strategy import Strategy, SpeakReview
from src.core.types.player import PlayerMemory

# Import VLLM Client manually
from src.core.llm.vllm_client import VLLMLangChainClient

def create_real_llm_client(output_model):
    # Using the model running in vllm
    return VLLMLangChainClient(model="google/gemma-3-12b-it", output_model=output_model)

def run_verification():
    print("=== Starting Pronoun Ban Verification ===")

    try:
        reviewer = SpeakReviewer(llm=create_real_llm_client(SpeakReview))
        refiner = SpeakRefiner(llm=create_real_llm_client(Speak))
    except Exception as e:
        print(f"Failed to connect to LLM: {e}")
        return

    # Mock Data
    memory = PlayerMemory(
        self_name="太郎", 
        self_role="villager", 
        players=["太郎", "花子"], 
        observed_events=[], 
        role_beliefs={}
    )
    strategy = Strategy(
        action_stance="aggressive",
        primary_target="花子",
        main_claim="花子は怪しい",
        goals=["Suspect Hanako"],
        approach="Aggressive questioning",
        key_points=["Hanako is suspicious"]
    )

    # Test Case: Vague Pronoun Violation
    print("\n--- Test Case: Vague Pronoun Violation ---")
    speak_invalid = Speak(text="彼が言っていることはおかしいです。", text_candidates=[])
    print(f"Original Text: {speak_invalid.text}")
    
    review = reviewer.review(speak=speak_invalid, strategy=strategy, memory=memory)

    if review and review.needs_fix:
        print(f"✅ Review Step Passed: Detected violation. Reason: {review.reason}")
        print(f"Fix Instruction: {review.fix_instruction}")
        
        # Refine Step
        refined = refiner.refine(
            original=speak_invalid,
            strategy=strategy,
            review=review,
            memory=memory
        )
        # Check if refined speech contains forbidden words
        text = refined.text if refined else ""
        print(f"Refined Text: {text}")

        if refined and ("彼" not in text) and ("花子" in text or "太郎" in text): 
             # Ideally it replaces "彼" with "花子さん" (contextually implies target) or just a name.
             # Since strategy target is Hanako, it might infer Hanako.
             print(f"✅ Refine Step Passed: Refined correctly.")
        elif refined and "彼" not in text:
             print(f"⚠️ Refine Step Warning: Removed pronoun but maybe didn't insert correct name? Text: {text}")
        else:
             print(f"❌ Refine Step Failed: Refinement failed or still has pronoun. Result: {text}")

    else:
        print(f"❌ Review Step Failed: Violation NOT detected. Reason: {review.reason if review else 'None'}")


if __name__ == "__main__":
    run_verification()
