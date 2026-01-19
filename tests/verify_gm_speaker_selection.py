"""
Verify GM Speaker Selection Logic

This test uses a standalone implementation to verify the speaker selection logic
without requiring full module imports that trigger API key validation.
"""
import sys
import os

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from dataclasses import dataclass
from typing import Optional, Any


@dataclass
class GameEvent:
    event_type: str
    payload: dict[str, Any]


def get_next_speaker(
    players: list[str],
    speak_counts: dict[str, int],
    last_speaker: Optional[str],
    recent_events: list[GameEvent],
) -> tuple[str, str]:
    """
    シンプルなラウンドロビン + 文脈補助による発言者選定。
    (Copied from gm_comment_generator.py for testing)
    """
    # 1. 未発言者リストを取得（プレイヤー順序を維持）
    unspoken = [p for p in players if speak_counts.get(p, 0) == 0]
    
    # 2. 全員発言済みなら新ラウンド開始
    if not unspoken:
        unspoken = list(players)
    
    # 3. 直前発言者を除外（連続指名防止）
    candidates = [p for p in unspoken if p != last_speaker]
    if not candidates:
        candidates = unspoken
    
    # 4. 文脈ヒント: 直前の発言で名指しされた人がいれば優先
    mentioned = get_mentioned_player(recent_events, candidates)
    if mentioned:
        return mentioned, "mentioned_in_last_speech"
    
    # 5. デフォルト: 候補リストの先頭（順番通り）
    return candidates[0], "round_robin"


def get_mentioned_player(
    recent_events: list[GameEvent],
    candidates: list[str],
) -> Optional[str]:
    """
    直前の発言で名指しされたプレイヤーを候補から探す。
    (Copied from gm_comment_generator.py for testing)
    """
    if not recent_events:
        return None
    
    last_event = recent_events[-1]
    if last_event.event_type != "speak":
        return None
    
    text = last_event.payload.get("text", "")
    speaker = last_event.payload.get("player", "")
    
    for p in candidates:
        if p != speaker and p in text:
            return p
    
    return None


def test_prevent_consecutive_speaker():
    """
    Test that the GM does not select the same speaker consecutively.
    """
    players = ["PlayerA", "PlayerB", "PlayerC"]
    speak_counts = {"PlayerA": 1, "PlayerB": 1, "PlayerC": 0}
    last_speaker = "PlayerA"
    
    recent_events = [
        GameEvent(event_type="speak", payload={"player": "PlayerB", "text": "Hello"}),
        GameEvent(event_type="speak", payload={"player": "PlayerA", "text": "I am Player A"}),
    ]

    next_speaker, reason = get_next_speaker(players, speak_counts, last_speaker, recent_events)
    
    print(f"Next speaker: {next_speaker}, Reason: {reason}")

    if next_speaker == "PlayerA":
        print("FAIL: PlayerA (last speaker) was selected as next speaker")
        return False
    else:
        print("SUCCESS: PlayerA correctly excluded from next speaker selection")
        return True


def test_round_robin_order():
    """
    Test that the round-robin logic works correctly - 
    unspoken players should be selected first.
    """
    players = ["PlayerA", "PlayerB", "PlayerC", "PlayerD"]
    speak_counts = {"PlayerA": 1, "PlayerB": 1, "PlayerC": 0, "PlayerD": 0}
    last_speaker = "PlayerB"
    
    recent_events = [
        GameEvent(event_type="speak", payload={"player": "PlayerA", "text": "Hello"}),
        GameEvent(event_type="speak", payload={"player": "PlayerB", "text": "Hi there"}),
    ]

    next_speaker, reason = get_next_speaker(players, speak_counts, last_speaker, recent_events)
    
    print(f"Next speaker: {next_speaker}, Reason: {reason}")

    # PlayerC should be selected (first unspoken player)
    if next_speaker == "PlayerC":
        print("SUCCESS: PlayerC (first unspoken) correctly selected")
        return True
    elif next_speaker == "PlayerD":
        print("SUCCESS: PlayerD (unspoken) correctly selected")
        return True
    else:
        print("FAIL: Neither unspoken player was selected")
        return False


def test_mentioned_player_priority():
    """
    Test that a player mentioned in the last speech is prioritized
    (if they are in the unspoken candidates).
    """
    players = ["PlayerA", "PlayerB", "PlayerC", "PlayerD"]
    speak_counts = {"PlayerA": 1, "PlayerB": 0, "PlayerC": 0, "PlayerD": 0}
    last_speaker = "PlayerA"
    
    # PlayerA spoke and mentioned PlayerD
    recent_events = [
        GameEvent(event_type="speak", payload={"player": "PlayerA", "text": "PlayerDさんはどう思いますか？"}),
    ]

    next_speaker, reason = get_next_speaker(players, speak_counts, last_speaker, recent_events)
    
    print(f"Next speaker: {next_speaker}, Reason: {reason}")

    # PlayerD should be selected because they were mentioned
    if next_speaker == "PlayerD":
        print("SUCCESS: PlayerD (mentioned) correctly prioritized")
        if reason == "mentioned_in_last_speech":
            print("SUCCESS: Reason indicates mention")
        return True
    else:
        print(f"FAIL: PlayerD (mentioned) was not selected, got {next_speaker} instead")
        return False


def test_all_spoken_reset():
    """
    Test that when all players have spoken, the round resets.
    """
    players = ["PlayerA", "PlayerB", "PlayerC"]
    speak_counts = {"PlayerA": 1, "PlayerB": 1, "PlayerC": 1}
    last_speaker = "PlayerC"
    
    recent_events = [
        GameEvent(event_type="speak", payload={"player": "PlayerC", "text": "Done"}),
    ]

    next_speaker, reason = get_next_speaker(players, speak_counts, last_speaker, recent_events)
    
    print(f"Next speaker: {next_speaker}, Reason: {reason}")

    # Should select anyone except PlayerC (last speaker)
    if next_speaker != "PlayerC":
        print(f"SUCCESS: {next_speaker} selected after all players spoke (not last speaker)")
        return True
    else:
        print("FAIL: PlayerC (last speaker) was selected after reset")
        return False


if __name__ == "__main__":
    all_passed = True
    
    print("=== Test 1: Prevent Consecutive Speaker ===")
    all_passed &= test_prevent_consecutive_speaker()
    print()
    
    print("=== Test 2: Round Robin Order ===")
    all_passed &= test_round_robin_order()
    print()
    
    print("=== Test 3: Mentioned Player Priority ===")
    all_passed &= test_mentioned_player_priority()
    print()
    
    print("=== Test 4: All Spoken Reset ===")
    all_passed &= test_all_spoken_reset()
    print()
    
    if all_passed:
        print("✓ All tests passed!")
    else:
        print("✗ Some tests failed!")
        sys.exit(1)
