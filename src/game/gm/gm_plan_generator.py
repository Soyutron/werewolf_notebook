from src.core.types.phases import GameDefinition, WorldState
from src.core.llm.client import LLMClient
from src.core.memory.gm_plan import GMProgressionPlan
from src.core.llm.prompts.gm_plan import GM_PLAN_SYSTEM_PROMPT

class GMPlanGenerator:
    """
    夜フェーズにおいて、ゲーム全体の進行計画を生成するクラス。
    """

    def __init__(self, llm: LLMClient[GMProgressionPlan]):
        self.llm = llm

    def generate(self, world_state: WorldState, game_def: GameDefinition) -> GMProgressionPlan:
        """
        現在の WorldState と役職構成（定義）に基づき、進行計画を生成する。
        GM は個別の役職割り当てを知らない。
        """
        # プロンプトの構築
        # 役職構成（Role Distribution）とプレイヤー一覧のみ提示
        roles_text = ", ".join(game_def.role_distribution)
        players_text = ", ".join(world_state.players)
        
        user_content = f"""
# 現在の状況
## 役職構成（Role Distribution）
{roles_text}

## プレイヤー一覧
{players_text}

## ルール
（ワンナイト人狼の標準ルールに準拠）

この盤面における進行計画を立案してください。
"""

        # LLM へのリクエスト
        response: GMProgressionPlan = self.llm.generate(
            system=GM_PLAN_SYSTEM_PROMPT,
            prompt=user_content,
        )

        return response
