import unittest
from src.core.types import GMGraphState, GMInternalState, GameDecision, GameEvent, WorldState
from src.core.types.phases import GameDefinition
from src.graphs.gm.node.result_phase import result_phase_node
from collections import Counter

class TestVoteResult(unittest.TestCase):

    def create_mock_state(self, votes, assigned_roles, phase="vote") -> GMGraphState:
        internal = GMInternalState(
            night_pending=[],
            vote_pending=[],
            votes=votes
        )
        world_state = WorldState(
            phase=phase,
            players=list(assigned_roles.keys()),
            public_events=[]
        )
        decision = GameDecision()
        
        # Minimal GameDefinition
        game_def = GameDefinition(
            roles={},
            role_distribution=[],
            phases=["night", "day", "vote"]
        )
        
        return {
            "world_state": world_state,
            "decision": decision,
            "internal": internal,
            "game_def": game_def,
            "assigned_roles": assigned_roles
        }

    def test_result_phase_single_execution_villager_win(self):
        # Setup: 3 Villagers, 1 Werewolf. Werewolf gets most votes.
        votes = {
            "p1": "p4",
            "p2": "p4",
            "p3": "p4", # 3 votes for p4
            "p4": "p1"  # 1 vote for p1
        }
        assigned_roles = {
            "p1": "villager",
            "p2": "villager",
            "p3": "seer",
            "p4": "werewolf"
        }
        
        state = self.create_mock_state(votes, assigned_roles)
        new_state = result_phase_node(state)
        
        result = new_state["world_state"].result
        self.assertIsNotNone(result)
        self.assertEqual(result.winner, "village")
        self.assertIn("p4", result.executed_players)
        self.assertEqual(len(result.executed_players), 1)
        self.assertIsNone(new_state["decision"].next_phase)

    def test_result_phase_single_execution_werewolf_win(self):
        # Setup: Villager gets executed.
        votes = {
            "p1": "p2",
            "p2": "p1",
            "p3": "p2", # 2 votes for p2
            "p4": "p2"  # 3 votes for p2
        }
        assigned_roles = {
            "p1": "villager",
            "p2": "villager",
            "p3": "seer",
            "p4": "werewolf"
        }
        
        state = self.create_mock_state(votes, assigned_roles)
        new_state = result_phase_node(state)
        
        result = new_state["world_state"].result
        self.assertIsNotNone(result)
        self.assertEqual(result.winner, "werewolf")
        self.assertIn("p2", result.executed_players)

    def test_result_phase_tie_execution_village_win(self):
        # Setup: Tie between Villager(p2) and Werewolf(p4).
        votes = {
            "p1": "p4",
            "p2": "p4", # 2 votes for p4
            "p3": "p2", 
            "p4": "p2"  # 2 votes for p2
        }
        assigned_roles = {
            "p1": "villager",
            "p2": "villager",
            "p3": "seer",
            "p4": "werewolf"
        }
        
        state = self.create_mock_state(votes, assigned_roles)
        new_state = result_phase_node(state)
        
        result = new_state["world_state"].result
        self.assertIsNotNone(result)
        # If werewolf dies, village wins
        self.assertEqual(result.winner, "village")
        self.assertIn("p2", result.executed_players)
        self.assertIn("p4", result.executed_players)
        self.assertEqual(len(result.executed_players), 2)

    def test_result_phase_tie_execution_werewolf_win(self):
        # Setup: Tie between two villagers.
        votes = {
            "p1": "p2",
            "p2": "p1", # 1 vote for p1
            "p3": "p2", # 2 votes for p2
            "p4": "p1"  # 2 votes for p1
        }
        assigned_roles = {
            "p1": "villager",
            "p2": "villager",
            "p3": "seer",
            "p4": "werewolf"
        }
        
        state = self.create_mock_state(votes, assigned_roles)
        new_state = result_phase_node(state)
        
        result = new_state["world_state"].result
        self.assertIsNotNone(result)
        self.assertEqual(result.winner, "werewolf")
        self.assertIn("p1", result.executed_players)
        self.assertIn("p2", result.executed_players)

if __name__ == '__main__':
    unittest.main()
