# src/core/roles/role_registry.py
"""
役職レジストリ - 役職定義の中央管理

責務:
- 全役職の定義を一元管理
- 役職情報の動的登録・取得
- 新規役職追加時に既存コードの変更を不要にする

設計原則:
- Single Source of Truth: 役職に関する全情報はここから取得
- Open-Closed: 新規役職追加は register() のみで完結
- 既存の prompts/roles.py と types/roles.py との互換性を維持
"""

from typing import Dict, List, Optional
from pydantic import BaseModel


class RoleConfig(BaseModel):
    """
    役職の完全な設定定義。
    
    型定義（types/roles.py）とプロンプト定義（prompts/roles.py）を統合し、
    戦略アドバイスを追加した包括的な役職情報。
    """
    name: str  # 内部識別子 (例: "villager")
    display_name: Dict[str, str]  # 表示名 (例: {"ja": "村人", "en": "Villager"})
    day_side: str  # 昼の立場 ("village" / "werewolf")
    win_side: str  # 勝利条件の帰属 ("village" / "werewolf")
    description: str  # 役職の説明
    goal: str  # 勝利目標
    ability: str  # 特殊能力（なければ空文字）
    core_principle: str  # 役職の本質的な行動原則（1文）
    strategy_advice: str  # 戦略計画生成用の詳細アドバイス
    divine_result_as_role: Optional[str] = None  # 占われた時に見える役職名（None の場合は name を使用）
    ability_type: str = "none"  # 能力の種類 ("none", "seer", "werewolf", etc.)


class RoleRegistry:
    """
    役職定義の中央レジストリ。
    
    新規役職追加時は register() を呼び出すだけで完了。
    既存のジェネレータやプロンプトファイルの修正は不要。
    """
    
    def __init__(self):
        self._roles: Dict[str, RoleConfig] = {}
    
    def register(self, config: RoleConfig) -> None:
        """役職を登録する"""
        self._roles[config.name] = config
    
    def get(self, name: str) -> Optional[RoleConfig]:
        """役職設定を取得する"""
        return self._roles.get(name)
    
    def get_all_names(self) -> List[str]:
        """登録済み全役職名を取得する"""
        return list(self._roles.keys())
    
    def get_all(self) -> Dict[str, RoleConfig]:
        """全役職設定を取得する"""
        return self._roles.copy()
    
    def get_advice(self, name: str) -> str:
        """
        役職の戦略アドバイスを取得する。
        
        存在しない役職の場合は空文字を返す。
        """
        config = self._roles.get(name)
        return config.strategy_advice if config else ""
    
    def get_display_name(self, name: str, lang: str = "ja") -> str:
        """
        役職の表示名を取得する。
        
        Args:
            name: 役職の内部識別子
            lang: 言語コード ("ja" または "en")
        
        Returns:
            表示名。存在しない場合は内部識別子をそのまま返す。
        """
        config = self._roles.get(name)
        if not config:
            return name
        return config.display_name.get(lang, name)


# =============================================================================
# グローバルインスタンス
# =============================================================================

role_registry = RoleRegistry()


# =============================================================================
# デフォルト役職の登録
# =============================================================================

# 村人
role_registry.register(RoleConfig(
    name="villager",
    display_name={"ja": "村人", "en": "Villager"},
    day_side="village",
    win_side="village",
    description="特殊能力を持たない基本役職。議論と推理のみで人狼を見つける。",
    goal="人狼を処刑する",
    ability="",
    ability_type="none",
    core_principle="論理的な推論で人狼を見つけ出し、他者を説得する。",
    strategy_advice="""\
- **村人**として真実を語り、論理的な議論を展開してください。
- 他プレイヤーの矛盾を見抜き、人狼の可能性を推論してください。
- 「村人CO」で白いままでいることをアピールできます。
- 無理に情報を作り出さず、観察と推理に集中してください。
"""
))

# 占い師
role_registry.register(RoleConfig(
    name="seer",
    display_name={"ja": "占い師", "en": "Seer"},
    day_side="village",
    win_side="village",
    description="夜フェーズに一人のプレイヤーの役職を占うことができる。",
    goal="人狼を処刑する",
    ability="夜に1人の役職を確認できる",
    ability_type="seer",
    core_principle="確定情報を活用して、村を正しい投票へと導く。",
    strategy_advice="""\
- **占い師CO**して、占い結果を共有することで信頼を得られます。
- ただし、対抗COされる可能性があるため、タイミングを見極めてください。
- 結果に基づいて村を正しい投票へと導くことが最優先です。
- 人狼判定が出た場合は、積極的にその情報を共有してください。
"""
))

# 人狼
role_registry.register(RoleConfig(
    name="werewolf",
    display_name={"ja": "人狼", "en": "Werewolf"},
    day_side="village",  # 昼は村人として振る舞う
    win_side="werewolf",
    description="村を欺く敵陣営。処刑されないように振る舞う。",
    goal="処刑を回避して生き残る",
    ability="",
    ability_type="werewolf",
    core_principle="村人を欺き、投票による追放を回避する。",
    strategy_advice="""\
- **占い師CO（偽）** を行い、本物の占い師の信用を落とすことができます。
- または **村人として潜伏** し、疑いを他者に向けることも有効です。
- あえてCOを控え、沈黙を保つことで矛盾を避ける戦略もあります。
- 真の占い師に人狼判定されるリスクを常に意識してください。
"""
))

# 狂人
role_registry.register(RoleConfig(
    name="madman",
    display_name={"ja": "狂人", "en": "Madman"},
    day_side="village",  # 占い判定は村人
    win_side="werewolf",  # 勝利条件は人狼側
    description="人狼陣営の味方。占い判定は「村人」だが、勝利条件は人狼側。",
    goal="人狼の勝利に貢献する",
    ability="",
    ability_type="none",
    core_principle="誰が人狼か知らぬまま、混乱を招いて人狼を守る。",
    strategy_advice="""\
- **占い師CO（偽）** で嘘の情報を流し、場を混乱させることができます。
- または **村人CO** で潜伏し、村人の投票先を誤らせることも有効です。
- 人狼が誰かわからないため、無差別に混乱を招くことが目標です。
- 真の占い師を攻撃して信用を落とすことで、人狼を間接的に守れます。
""",
    divine_result_as_role="villager",  # 占われると村人に見える
))

# 怪盗
role_registry.register(RoleConfig(
    name="thief",
    display_name={"ja": "怪盗", "en": "Thief"},
    day_side="village",
    win_side="village",  # 初期状態は村人陣営（交換後に変わる可能性あり）
    description="夜フェーズに他プレイヤーと役職を交換できる。交換後はその役職として扱われる。",
    goal="人狼を処刑する（交換後の役職に依存）",
    ability="夜に1人と役職を交換できる",
    ability_type="thief",
    core_principle="役職交換により有利な立場を得て、最終勝利を目指す。",
    strategy_advice="""\
- **役職交換**により、自分の役職を確認しつつ相手の役職を奪えます。
- 交換後は新しい役職の勝利条件に従います。
- 人狼と交換した場合、あなたは人狼陣営になります。
- 占い師と交換した場合、あなたは占い結果を持っていない占い師になります。
- 村人と交換した場合、特に変化はありませんが相手の役職を確認できます。
"""
))


# =============================================================================
# 便利なヘルパー関数（後方互換性のため）
# =============================================================================

def get_all_role_names() -> List[str]:
    """登録済み全役職名を取得する"""
    return role_registry.get_all_names()


def get_role_config(name: str) -> Optional[RoleConfig]:
    """役職設定を取得する"""
    return role_registry.get(name)


def get_role_advice(name: str) -> str:
    """役職の戦略アドバイスを取得する"""
    return role_registry.get_advice(name)


def get_role_display_name(name: str, lang: str = "ja") -> str:
    """役職の表示名を取得する"""
    return role_registry.get_display_name(name, lang)
