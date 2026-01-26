import unittest
from src.core.types import GMGraphState, GMInternalState, GameDecision, GameEvent, WorldState
from src.core.types.phases import GameDefinition
from src.graphs.gm.node.result_phase import result_phase_node
from src.core.types.roles import RoleDefinition
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
        
        # Populate Role Definitions
        roles = {
            "villager": RoleDefinition(name="villager", day_side="village", win_side="village"),
            "seer": RoleDefinition(name="seer", day_side="village", win_side="village"),
            "werewolf": RoleDefinition(name="werewolf", day_side="werewolf", win_side="werewolf"),
            "madman": RoleDefinition(name="madman", day_side="village", win_side="werewolf"),
        }
        
        # Minimal GameDefinition
        game_def = GameDefinition(
            roles=roles,
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

    def test_result_phase_all_one_vote_peaceful_rule(self):
        # Setup: Everyone gets 1 vote. No execution.
        # Case 1: Werewolf exists -> Werewolf Wins
        votes = {
            "p1": "p2",
            "p2": "p3",
            "p3": "p4",
            "p4": "p1"
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
        self.assertEqual(len(result.executed_players), 0) # No execution
        self.assertEqual(result.winner, "werewolf") # Werewolf safe

    def test_result_phase_peaceful_village_success(self):
        # Setup: No werewolf in game. Everyone gets 1 vote.
        # Village Wins.
        votes = {
            "p1": "p2",
            "p2": "p3",
            "p3": "p4",
            "p4": "p1"
        }
        assigned_roles = {
            "p1": "villager",
            "p2": "villager",
            "p3": "seer",
            "p4": "villager" # No werewolf
        }
        state = self.create_mock_state(votes, assigned_roles)
        new_state = result_phase_node(state)
        
        result = new_state["world_state"].result
        self.assertEqual(len(result.executed_players), 0)
        self.assertEqual(result.winner, "village")

    def test_result_phase_peaceful_village_fail(self):
        # Setup: No werewolf in game. But someone is executed (max votes > 1).
        # Village Loses (Werewolf Wins by default rule of killing innocent in peaceful village? 
        # Actually standard One Night rule: "Only if NO ONE dies do villagers win." -> If someone dies, Villagers lose -> Werewolf wins.)
        votes = {
            "p1": "p2",
            "p2": "p1",
            "p3": "p2", # p2 has 2 votes
            "p4": "p1"  # p1 has 2 votes
        }
        # Tie break executes p1 and p2.
        
        assigned_roles = {
            "p1": "villager",
            "p2": "villager",
            "p3": "seer",
            "p4": "villager"
        }
        state = self.create_mock_state(votes, assigned_roles)
        new_state = result_phase_node(state)
        
        result = new_state["world_state"].result
        self.assertTrue(len(result.executed_players) > 0)
        self.assertEqual(result.winner, "werewolf")

if __name__ == '__main__':
    unittest.main()
