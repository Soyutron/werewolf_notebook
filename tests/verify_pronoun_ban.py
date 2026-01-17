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
    return VLLMLangChainClient(model="google/gemma-3-12b-it", output_model=output_model)

def run_verification():
    print("=== Starting Name Preservation & Pronoun Fix Verification ===")

    try:
        reviewer = SpeakReviewer(llm=create_real_llm_client(SpeakReview))
        refiner = SpeakRefiner(llm=create_real_llm_client(Speak))
    except Exception as e:
        print(f"Failed to connect to LLM: {e}")
        return

    # Scenario 1: Valid Speech with Name (Should PASS)
    # Speaker: Hanako (Seer)
    # Target: Taro
    # Input: "I am Seer. I divined Taro."
    print("\n--- Test Case 1: Valid Name Usage (Preservation) ---")
    
    memory_hanako = PlayerMemory(
        self_name="花子", 
        self_role="seer", 
        players=["太郎", "花子", "次郎"], 
        observed_events=[], 
        role_beliefs={}
    )
    strategy_hanako = Strategy(
        action_stance="aggressive",
        co_decision="co_now",
        co_target="太郎",
        co_result="人狼",
        primary_target="太郎",
        main_claim="太郎は村人だ",
        goals=["Reveal result"],
        approach="CO as Seer",
        key_points=["Divined Taro", "Result is Villager"]
    )
    
    speak_valid = Speak(text="私は占い師です。太郎さんを占いました。", text_candidates=[])
    print(f"Original Text: {speak_valid.text}")

    review1 = reviewer.review(speak=speak_valid, strategy=strategy_hanako, memory=memory_hanako)

    if review1 and not review1.needs_fix:
        print(f"✅ Review Step Passed: Correctly identified valid speech. (needs_fix=False)")
    else:
        print(f"❌ Review Step Failed: False Positive! Reason: {review1.reason if review1 else 'None'}")
        if review1:
            print("Attempting to Refine anyway to check safety...")
            refined1 = refiner.refine(
                original=speak_valid,
                strategy=strategy_hanako,
                review=review1,
                memory=memory_hanako
            )
            print(f"Refined Text: {refined1.text if refined1 else 'None'}")

    
    # Scenario 2: Invalid Pronoun Usage (Should FIX correctly)
    # Speaker: Hanako
    # Target: Taro
    # Input: "彼は人狼だと思います" (I think he is werewolf)
    print("\n--- Test Case 2: Ambiguous Pronoun (Correction) ---")
    speak_invalid = Speak(text="彼は人狼だと思います。", text_candidates=[])
    print(f"Original Text: {speak_invalid.text}")
    
    review2 = reviewer.review(speak=speak_invalid, strategy=strategy_hanako, memory=memory_hanako)
    
    if review2 and review2.needs_fix:
        print(f"✅ Review Step Passed: Detected violation. Reason: {review2.reason}")
        
        refined2 = refiner.refine(
            original=speak_invalid,
            strategy=strategy_hanako,
            review=review2,
            memory=memory_hanako
        )
        text2 = refined2.text if refined2 else ""
        print(f"Refined Text: {text2}")
        
        if "彼" not in text2 and "太郎" in text2:
            print(f"✅ Refine Step Passed: Replaced '彼' with '太郎'.")
        else:
            print(f"❌ Refine Step Failed: Did not replace strictly or completely. Text: {text2}")

    else:
        print(f"❌ Review Step Failed: Failed to detect pronoun. Reason: {review2.reason if review2 else 'None'}")

if __name__ == "__main__":
    run_verification()
