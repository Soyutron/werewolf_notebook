import sys
import unittest
from src.core.memory.strategy import Strategy, TurnAction, COContent

class TestNewStrategyStructure(unittest.TestCase):
    def test_turn_action_structure(self):
        """Test TurnAction and COContent creation"""
        co = COContent(
            role="seer",
            result="werewolf",
            target="Bob",
            reason="Found wolf"
        )
        action = TurnAction(
            action_type="co",
            trigger="immediate",
            target_player="Alice",
            description="Reveal result",
            co_content=co,
            pressure=8
        )
        self.assertEqual(action.action_type, "co")
        self.assertEqual(action.co_content.role, "seer")
        self.assertEqual(action.pressure, 8)

    def test_strategy_structure(self):
        """Test complete Strategy object creation"""
        main_action = TurnAction(
            action_type="vote_inducement",
            trigger="proactive",
            target_player="Charlie",
            description="Push for Charlie execution"
        )
        
        counter_action = TurnAction(
            action_type="disagree",
            trigger="reactive_counter",
            target_player="Dave",
            description="Deny accusation"
        )
        
        strategy = Strategy(
            main_action=main_action,
            conditional_actions=[counter_action],
            style_focus="aggression",
            text_style="Assertive",
            current_priority="Eliminate wolf"
        )
        
        self.assertEqual(strategy.kind, "strategy")
        self.assertEqual(strategy.main_action.target_player, "Charlie")
        self.assertEqual(len(strategy.conditional_actions), 1)
        self.assertEqual(strategy.get_co_action(), None)

    def test_get_co_action(self):
        """Test get_co_action helper"""
        co_action = TurnAction(
            action_type="co",
            trigger="immediate",
            description="CO now",
            co_content=COContent(role="medium")
        )
        strategy = Strategy(
            main_action=co_action,
            style_focus="logic",
            text_style="Calm",
            current_priority="Info"
        )
        self.assertIsNotNone(strategy.get_co_action())
        self.assertEqual(strategy.get_co_action().co_content.role, "medium")

if __name__ == '__main__':
    unittest.main()
