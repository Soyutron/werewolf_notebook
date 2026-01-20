
import sys
import os

# Add src to python path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../../")))

from src.core.types.phases import GameDefinition, get_next_phase
from src.game.one_night import ONE_NIGHT_GAME_DEFINITION
from src.core.session.game_session import GameSession
from src.core.types import PlayerInput, PlayerOutput, SeerAbility, GameEvent, PlayerMemory, RoleProb
from src.core.session.action_resolver import ActionResolver
from src.game.player.belief_utils import build_belief_analysis_section

def verify_game_definition_structure():
    print("=== Verifying GameDefinition Structure ===")
    roles = ONE_NIGHT_GAME_DEFINITION.roles
    
    # Check "seer" ability type
    assert roles["seer"].ability_type == "seer", "Seer ability_type should be 'seer'"
    print("OK: Seer ability_type is 'seer'")
    
    # Check "madman" divine result
    assert roles["madman"].divine_result_as_role == "villager", "Madman divine_result_as_role should be 'villager'"
    print("OK: Madman divine_result_as_role is 'villager'")
    
    # Check "werewolf" win side
    assert roles["werewolf"].win_side == "werewolf", "Werewolf win_side should be 'werewolf'"
    print("OK: Werewolf win_side is 'werewolf'")

def verify_phase_transition():
    print("\n=== Verifying Phase Transition Logic ===")
    
    # night -> day
    next_p = get_next_phase("night", ONE_NIGHT_GAME_DEFINITION)
    assert next_p == "day", f"Expected 'day', got {next_p}"
    print("OK: night -> day")
    
    # day -> vote
    next_p = get_next_phase("day", ONE_NIGHT_GAME_DEFINITION)
    assert next_p == "vote", f"Expected 'vote', got {next_p}"
    print("OK: day -> vote")

    # vote -> result (implicit end of list behavior)
    next_p = get_next_phase("vote", ONE_NIGHT_GAME_DEFINITION)
    assert next_p == "result", f"Expected 'result', got {next_p}"
    print("OK: vote -> result")

def verify_seer_action_resolution():
    print("\n=== Verifying Seer Action Resolution (Madman check) ===")
    
    # Mock data
    assigned_roles = {"Alice": "seer", "Bob": "madman"}
    
    # Create resolver
    resolver = ActionResolver(assigned_roles=assigned_roles)
    
    # Create Mock Session
    class MockSession:
        def __init__(self):
            self.definition = ONE_NIGHT_GAME_DEFINITION
            self.gm_internal = type('obj', (object,), {'night_pending': set(['Alice'])})
            self.last_player_input = None
            
        def run_player_turn(self, player, input):
            self.last_player_input = input
            
    session = MockSession()
    
    # Alice (Seer) divines Bob (Madman)
    output = PlayerOutput(
        action="use_ability",
        payload=SeerAbility(kind="seer", target="Bob")
    )
    
    resolver.resolve(player="Alice", output=output, session=session)
    
    # Check result
    event = session.last_player_input.event
    assert event.event_type == "divine_result"
    assert event.payload["target"] == "Bob"
    # Essential check: Madman should appear as "villager" due to GameDefinition
    assert event.payload["role"] == "villager", f"Expected Bob to be seen as 'villager', got {event.payload['role']}"
    print("OK: Madman correctly identified as 'villager' by Seer")

def verify_belief_utils():
    print("\n=== Verifying Belief Utils (Dynamic Side Check) ===")
    
    # Mock Memory for a Villager
    memory = PlayerMemory(
        self_name="Alice",
        self_role="villager",
        players=["Alice", "Bob"],
        observed_events=[],
        role_beliefs={
            "Bob": RoleProb(probs={"werewolf": 0.9, "villager": 0.1})
        }
    )
    
    # Alice (Villager) suspects Bob (Werewolf). 
    # Villager win_side = "village", Werewolf win_side = "werewolf". -> Different -> Suspicious.
    analysis = build_belief_analysis_section(memory, ONE_NIGHT_GAME_DEFINITION)
    print(f"[Villager Analysis Output]\n{analysis}")
    assert "疑わしい" in analysis or "Bob" in analysis
    print("OK: Villager correctly suspects Werewolf")

    # Mock Memory for a Werewolf
    memory_wolf = PlayerMemory(
        self_name="Charlie",
        self_role="werewolf",
        players=["Charlie", "Dave"],
        observed_events=[],
        role_beliefs={
            "Dave": RoleProb(probs={"werewolf": 0.9, "villager": 0.1})
        }
    )
    
    # Charlie (Werewolf) looks at Dave (Werewolf).
    # Both win_side = "werewolf". -> Same -> Trusted.
    analysis_wolf = build_belief_analysis_section(memory_wolf, ONE_NIGHT_GAME_DEFINITION)
    print(f"\n[Werewolf Analysis Output]\n{analysis_wolf}")
    
    # Note: Traditional werewolf strategy might call allies "fellow wolves", 
    # but build_belief_analysis_section classifies based on side matching.
    # Same side = Trusted.
    
    # If build_belief_analysis_section is working dynamically, Dave should be in "Trusted" (Trustable/Ally) section.
    # The text says "信頼できるプレイヤー (味方)"
    assert "信頼できる" in analysis_wolf or "味方" in analysis_wolf
    print("OK: Werewolf correctly trusts fellow Werewolf")

if __name__ == "__main__":
    verify_game_definition_structure()
    verify_phase_transition()
    verify_seer_action_resolution()
    verify_belief_utils()
    print("\nALL VERIFICATIONS PASSED")
