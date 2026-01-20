
import sys
import os

# Add src to python path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../../")))

from src.core.session.game_session import GameSession
from src.game.one_night import ONE_NIGHT_GAME_DEFINITION
from src.core.types import PlayerInput

def verify_session_injection():
    print("=== Verifying GameDefinition Injection into PlayerState ===")
    
    player_names = ["Alice", "Bob", "Charlie", "Dave"]
    
    # Initialize session
    # We will mock the graph execution by inspecting run_player_turn's working_state
    # Or actually running it. Running it requires LLM config mock.
    
    # Let's inspect GameSession.run_player_turn behavior through a subclass or override?
    # No, let's just make a Dummy Player Controller execution.
    
    # Actually, we can just instantiate GameSession and call run_player_turn manually and check if it crashes?
    # But run_player_turn creates working_state and passes it to controller.
    # The crash happens INSIDE the controller's graph execution (specifically use_ability node).
    
    # So we need to mock the controller or graph logic.
    # But simpler: run a real session but spy on it?
    
    # Let's try to just run a small test that calls run_night_phase without real LLMs if possible.
    # "GameSession" uses "create_player_controller" ...
    
    # If I cannot easily run full graph due to LLM requirements, 
    # I can at least verify that run_player_turn populates the key.
    
    session = GameSession.create(
        definition=ONE_NIGHT_GAME_DEFINITION,
    )
    
    player_names = session.world_state.players
    
    print("Session created.")
    
    # Monkey-patch controller.act to check for game_def
    original_act = None
    
    def mock_act(state):
        print(f"Mock act called for {state['memory'].self_name}")
        if "game_def" not in state:
            print("ERROR: game_def MISSING in state passed to controller!")
            raise RuntimeError("game_def missing")
        elif state["game_def"] is None:
            print("ERROR: game_def is None!")
            raise RuntimeError("game_def is None")
        else:
            print("SUCCESS: game_def found in state.")
            # Verify it is the correct object
            assert state["game_def"] == ONE_NIGHT_GAME_DEFINITION
            print("SUCCESS: game_def matches definition.")
            
        return state # Return state as is
        
    # Patch the controllers
    for player in player_names:
        # Assuming session.controllers is a dict or something accessible?
        # GameSession._dispatcher uses session.player_states.
        # But where are controllers stored?
        # Session doesn't expose controllers publicly easily?
        # session.controllers is a dict?
        pass
        
    if hasattr(session, "controllers"):
        for p in session.controllers:
            # Each controller has act method?
            # session.controllers[p].act = mock_act
            # But method binding...
            pass
            
    # Wait, session.run_player_turn accesses self.controllers[player].act
    # So I can patch it.
    
    # However, Session.controllers is NOT public in type hint, but usually accessible in python.
    # Let's check `session.controllers`. 
    # Wait, GameSession implementation in file:
    # self.controllers: Dict[PlayerName, PlayerController] = ...
    
    # So I can patch it.
    for p in player_names:
         # Need to bind the mock_act to instance or just replace the method on the instance?
         # controller is an instance.
         # session.controllers[p].act = partial(mock_act) # No, act takes (state=...)
         
         # Just replace the callable
         session.controllers[p].act = mock_act
         
    print("Patched controllers. Running player turn manually...")
    
    # Run a dummy turn
    session.run_player_turn(
        player=player_names[0],
        input=PlayerInput(request={"request_type": "use_ability", "payload": {}})
    )
    
    print("Verification complete.")

if __name__ == "__main__":
    verify_session_injection()
