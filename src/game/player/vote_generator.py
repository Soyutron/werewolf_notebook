from typing import Optional, Union

from src.core.llm.client import LLMClient
from src.core.llm.prompts import ONE_NIGHT_WEREWOLF_RULES
from src.core.memory.vote import VoteOutput
from src.core.types import (
    PlayerMemory,
    GameEvent,
    PlayerRequest,
    Vote,
)
from src.config.llm import create_vote_llm


Observed = Union[GameEvent, PlayerRequest]


class VoteGenerator:
    """
    PlayerMemory と新しく観測したイベントから
    投票先（Vote）を生成するクラス。

    設計方針:
    - vote は主観的な意思決定
    - 推理・判断ロジックはすべて LLM に委譲
    - state は直接変更しない
    - LLM が失敗した場合は None を返す
    """

    def __init__(self, llm: LLMClient[VoteOutput]):
        self.llm = llm

    def generate(
        self,
        *,
        memory: PlayerMemory,
        observed: Observed,
    ) -> Optional[Vote]:
        """
        投票先を1人生成する。

        失敗した場合は None を返す。
        """
        prompt = self._build_prompt(memory, observed)

        try:
            result: VoteOutput = self.llm.generate(
                prompt=prompt,
            )

            return Vote(
                voter=memory.self_name,
                target=result.target,
            )

        except Exception:
            # 投票生成に失敗してもゲーム進行は止めない
            return None

    def _build_prompt(
        self,
        memory: PlayerMemory,
        observed: Observed,
    ) -> str:
        """
        投票判断用の prompt を構築する。

        - belief / 発言履歴 / 確定情報を総合して判断させる
        - 理由は出力させない（純粋な行動のみ）
        """
        observed_type = observed.__class__.__name__

        current_beliefs = "\n".join(
            f"- {player}: {belief.probs}"
            for player, belief in memory.role_beliefs.items()
        )

        discussion_history = "\n".join(f"- {e}" for e in reversed(memory.history))

        from src.core.llm.prompts.roles import get_role_goal

        role_goal = get_role_goal(memory.self_role)

        return f"""
{ONE_NIGHT_WEREWOLF_RULES}

Your task is to decide **who to vote for**.

Current players:
{memory.players}

Your own name:
{memory.self_name}

Your own role (fixed, secret):
{memory.self_role}

Your Goal:
{role_goal}

Your private role beliefs:
{current_beliefs}

Discussion history (public actions and statements):
{discussion_history}

New observation:
Type: {observed_type}
Details:
{observed.model_dump()}

Rules:
- Choose exactly ONE player to vote for.
- You CANNOT vote for yourself.
- Vote for the player that helps you achieve your Goal: {role_goal}
- Do NOT explain your reasoning.
- Output JSON only.

Output format:
{{
  "target": "Alice"
}}
"""


# --- グローバルに1つだけ ---
vote_generator = VoteGenerator(llm=create_vote_llm())
