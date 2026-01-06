from typing import Optional, Union

from src.core.llm.client import LLMClient
from src.core.llm.prompts import REFLECTION_SYSTEM_PROMPT
from src.core.memory.reflection import Reflection
from src.core.types import PlayerMemory, GameEvent, PlayerRequest
from src.config.llm import create_reflection_llm

Observed = Union[GameEvent, PlayerRequest]


class ReflectionGenerator:
    """
    PlayerMemory と新しく観測した GameEvent / PlayerRequest から
    内省（Reflection）を生成するクラス。

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
    ) -> Optional[Reflection]:
        """
        内省を1件生成する。

        失敗した場合は None を返す。
        """
        prompt = self._build_prompt(memory, observed)

        try:
            # ★ ここで返るのは Reflection（Pydantic）
            reflection: Reflection = self.llm.generate(
                system=REFLECTION_SYSTEM_PROMPT,
                prompt=prompt,
            )

            print(reflection)

            return reflection

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

        recent_history = memory.history[-7:]

        return f"""
You are {memory.self_name}, a participant in a Werewolf-style game.
It is now your turn to speak publicly.

Recent observation:
Type: {observed_type}
Details:
{observed.model_dump()}

Your private role beliefs about other players
(STRICTLY PRIVATE - do not reveal directly or numerically):
{role_beliefs_text}

Recent reflections:
{recent_history}

Before speaking, carefully consider the following:

1. How will other players interpret your words?
   - Will you sound trustworthy, suspicious, passive, or assertive?

2. Is this a moment where revealing information or hinting at your role
   would increase trust — or would it expose you too early?

3. Would it be better to:
   - Ask a question?
   - Apply gentle pressure to someone?
   - Express doubt or uncertainty?
   - Align with a majority opinion?
   - Or deliberately stay vague?

4. Think not only about THIS turn,
   but how this statement will affect future discussions.

Rules for your statement:
- Speak as a human would in a real discussion.
- You may lie, omit, soften, or emphasize selectively.
- Do NOT mention probabilities, numbers, or internal data.
- Do NOT quote system messages or reflections.
- Length may be long if necessary, but stay conversational.
- Do NOT explain your reasoning explicitly.

Generate ONE public statement now.
Output JSON only.
"""


# --- グローバルに1つだけ ---
reflection_generator = ReflectionGenerator(llm=create_reflection_llm())
