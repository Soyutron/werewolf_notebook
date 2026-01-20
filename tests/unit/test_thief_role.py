"""
怪盜（Thief）役職のユニットテスト

テスト項目:
- 怪盗がRoleRegistryに正しく登録されているか
- ThiefAbilityモデルの動作確認
- 能力優先度の確認
"""

import unittest


class TestThiefRole(unittest.TestCase):
    """怪盗役職に関するテスト"""

    def test_thief_registered_in_registry(self):
        """怪盗がRoleRegistryに登録されているか確認"""
        from src.core.roles import get_role_config, get_all_role_names
        
        # 役職リストに含まれているか
        self.assertIn("thief", get_all_role_names())
        
        # 設定を取得できるか
        config = get_role_config("thief")
        self.assertIsNotNone(config)
        self.assertEqual(config.name, "thief")
        self.assertEqual(config.ability_type, "thief")
        self.assertEqual(config.win_side, "village")
        self.assertEqual(config.day_side, "village")

    def test_thief_display_name(self):
        """怪盗の表示名を確認"""
        from src.core.roles import get_role_display_name
        
        self.assertEqual(get_role_display_name("thief", "ja"), "怪盗")
        self.assertEqual(get_role_display_name("thief", "en"), "Thief")

    def test_thief_ability_model(self):
        """ThiefAbilityモデルの動作確認"""
        from src.core.types.player import ThiefAbility
        
        ability = ThiefAbility(kind="thief", target="Bob")
        self.assertEqual(ability.kind, "thief")
        self.assertEqual(ability.target, "Bob")

    def test_thief_ability_in_union(self):
        """ThiefAbilityがAbilityResult Unionに含まれているか確認"""
        from src.core.types.player import AbilityResult, ThiefAbility
        from typing import get_args
        
        # AbilityResult の Union 型引数を取得
        union_types = get_args(AbilityResult)
        self.assertIn(ThiefAbility, union_types)


class TestAbilityPriorityOrder(unittest.TestCase):
    """能力実行優先度に関するテスト"""

    def test_ability_priority_ordering(self):
        """能力優先度が正しく設定されているか確認"""
        from src.graphs.gm.node.night_phase import ABILITY_PRIORITY, get_ability_priority
        
        # 占い師が最優先
        self.assertEqual(get_ability_priority("seer"), 1)
        # 怪盗は2番目
        self.assertEqual(get_ability_priority("thief"), 2)
        # 人狼とその他は最後
        self.assertEqual(get_ability_priority("werewolf"), 3)
        self.assertEqual(get_ability_priority("none"), 3)
        # 未知の能力も最後
        self.assertEqual(get_ability_priority("unknown"), 3)


if __name__ == "__main__":
    unittest.main()
