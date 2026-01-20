import unittest
from src.core.roles import (
    role_registry,
    RoleConfig,
    get_all_role_names,
    get_role_config,
    get_role_advice,
    get_role_display_name,
)

class TestRoleRegistry(unittest.TestCase):
    def setUp(self):
        # テスト用にレジストリの状態をバックアップ（本来はシングルトンなので注意が必要）
        # しかし RoleRegistry は追加のみで削除がないため、
        # 追加したテスト用役職が他のテストに影響しないようにユニークな名前を使う
        pass

    def test_default_roles_exist(self):
        """デフォルトの役職が登録されているか確認"""
        roles = get_all_role_names()
        self.assertIn("villager", roles)
        self.assertIn("seer", roles)
        self.assertIn("werewolf", roles)
        self.assertIn("madman", roles)

    def test_get_role_config(self):
        """役職設定の取得機能を確認"""
        config = get_role_config("seer")
        self.assertIsNotNone(config)
        self.assertEqual(config.name, "seer")
        self.assertEqual(config.win_side, "village")
        self.assertIn("夜フェーズ", config.description)

    def test_get_role_advice(self):
        """戦略アドバイスの取得機能を確認"""
        advice = get_role_advice("werewolf")
        self.assertIn("占い師CO（偽）", advice)
        
        # 存在しない役職
        empty_advice = get_role_advice("non_existent_role")
        self.assertEqual(empty_advice, "")

    def test_register_new_role(self):
        """新規役職の登録と取得を確認"""
        new_role = RoleConfig(
            name="hunter",
            display_name={"ja": "狩人", "en": "Hunter"},
            day_side="village",
            win_side="village",
            description="処刑されたときに道連れにできる",
            goal="人狼処刑",
            ability="道連れ",
            core_principle="村を守るために命を使う",
            strategy_advice="潜伏して人狼を狙え"
        )
        
        role_registry.register(new_role)
        
        # 取得確認
        fetched = get_role_config("hunter")
        self.assertEqual(fetched.name, "hunter")
        self.assertEqual(fetched.ability, "道連れ")
        
        # リストに含まれるか
        self.assertIn("hunter", get_all_role_names())
        
        # 表示名
        self.assertEqual(get_role_display_name("hunter", "ja"), "狩人")
        self.assertEqual(get_role_display_name("hunter", "en"), "Hunter")

    def test_get_role_display_name_fallback(self):
        """表示名のフォールバック確認"""
        name = get_role_display_name("unknown_role")
        self.assertEqual(name, "unknown_role")

if __name__ == '__main__':
    unittest.main()
