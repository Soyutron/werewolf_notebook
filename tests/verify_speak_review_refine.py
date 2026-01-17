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
    print("=== Starting Speak Review/Refine Verification ===")

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
        main_claim="花子は情報を持たないまま潜伏している",
        goals=["Suspect Hanako"],
        approach="Aggressive questioning",
        key_points=["Hanako is too quiet", "Ask for her role"]
    )

    # Test Case 1: Valid Speech
    print("\n--- Test Case 1: Valid Speech ---")
    speak_valid = Speak(text="花子さん、なぜそんなに静かなんですか？役職を教えてください。", text_candidates=[])
    review_1 = reviewer.review(speak=speak_valid, strategy=strategy, memory=memory)
    
    if review_1 and not review_1.needs_fix:
        print("✅ Case 1 Passed: Valid speech accepted.")
    else:
        print(f"❌ Case 1 Failed: Valid speech rejected. Reason: {review_1.reason if review_1 else 'None'}")

    # Test Case 2: Self-Reference Violation
    print("\n--- Test Case 2: Self-Reference Violation ---")
    speak_invalid = Speak(text="太郎は花子さんが怪しいと思います。", text_candidates=[])
    review_2 = reviewer.review(speak=speak_invalid, strategy=strategy, memory=memory)

    if review_2 and review_2.needs_fix:
        print(f"✅ Case 2 Step 1 Passed: Detected violation. Reason: {review_2.reason}")
        
        # Refine Step
        refined_2 = refiner.refine(
            original=speak_invalid,
            strategy=strategy,
            review=review_2,
            memory=memory
        )
        # Check if refined speech contains forbidden words
        text = refined_2.text if refined_2 else ""
        if refined_2 and "太郎" not in text:
             print(f"✅ Case 2 Step 2 Passed: Refined correctly (removed self-ref): {text}")
        else:
             print(f"❌ Case 2 Step 2 Failed: Refinement failed or still has self-ref. Result: {text}")

    else:
        print(f"❌ Case 2 Step 1 Failed: Violation NOT detected. Reason: {review_2.reason if review_2 else 'None'}")

    # Test Case 3: Strategy 'Mismatch' (Should be ignored now)
    print("\n--- Test Case 3: Weak Strategy Alignment (Should PASS) ---")
    # Strategy is aggressive, but speech is weak. 
    # Old behavior: Reject (most likely). New behavior: Accept.
    speak_weak = Speak(text="うーん、花子さん、どうなんだろう...", text_candidates=[])
    review_3 = reviewer.review(speak=speak_weak, strategy=strategy, memory=memory)

    if review_3 and not review_3.needs_fix:
        print("✅ Case 3 Passed: Weak speech accepted (Reviewer is not quality police).")
    else:
        print(f"❌ Case 3 Failed: Weak speech rejected. Reason: {review_3.reason if review_3 else 'None'}")

if __name__ == "__main__":
    run_verification()
