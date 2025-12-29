from typing import Optional, Union

from src.core.llm.client import LLMClient
from src.core.llm.prompts import REACTION_SYSTEM_PROMPT
from src.core.memory.reaction import Reaction
from src.core.types import PlayerMemory, GameEvent, PlayerRequest
from src.config.llm import create_reaction_llm

Observed = Union[GameEvent, PlayerRequest]


class ReactionGenerator:
    """
    PlayerMemory と新しく観測した GameEvent / PlayerRequest から
    反応（Reaction）を生成するクラス。

    設計方針:
    - ゲームロジックに影響しない
    - 副作用を持たない（state を直接変更しない）
    - LLM が失敗しても None を返すだけ
    """

    def __init__(self, llm: LLMClient):
        self.llm = llm

    def generate(
        self,
        *,
        memory: PlayerMemory,
        observed: Observed,
    ) -> Optional[Reaction]:
        """
        反応を1件生成する。

        失敗した場合は None を返す。
        """
        prompt = self._build_prompt(memory, observed)

        try:
            # ★ ここで返るのは Reaction（Pydantic）
            reaction: Reaction = self.llm.generate(
                system=REACTION_SYSTEM_PROMPT,
                prompt=prompt,
            )

            print(reaction)

            return reaction

        except Exception:
            # LLM / validation が壊れてもゲームは止めない
            # 必要なら logging.debug(e)
            return None

    def _build_prompt(
        self,
        memory: PlayerMemory,
        observed: Observed,
    ) -> str:
        """
        内省用の user prompt を構築する。

        ここでは:
        - 新しいイベント
        - 現在の役職確率
        - 直近の内省
        だけを渡す
        """
        observed_type = observed.__class__.__name__

        role_beliefs_text = "\n".join(
            f"- {player}: {belief.probs}"
            for player, belief in memory.role_beliefs.items()
        )

        recent_history = memory.history[-3:]

        return f"""
You are {memory.self_name}.
Your role is {memory.self_role}.

New observation you perceived:
Type: {observed_type}
Details:
{observed.model_dump()}

Current role beliefs:
{role_beliefs_text}

Recent reactions:
{recent_history}

Write a new reflection in JSON.
"""


# --- グローバルに1つだけ ---
reaction_generator = ReactionGenerator(llm=create_reaction_llm())
