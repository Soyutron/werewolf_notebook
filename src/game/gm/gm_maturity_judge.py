from typing import Optional

from src.core.llm.client import LLMClient
from src.core.llm.prompts import GM_MATURITY_SYSTEM_PROMPT
from src.core.memory.gm_maturity import GMMaturityDecision
from src.core.types import GameEvent
from src.config.llm import create_gm_maturity_llm


def format_events_for_maturity(events: list[GameEvent]) -> str:
    return "\n".join(f"- [{e.event_type}] {e.payload}" for e in events)


class GMMaturityJudge:
    """
    GM が議論の成熟度を判定する。
    """

    def __init__(self, llm: LLMClient):
        self.llm = llm

    def judge(
        self,
        *,
        public_events: list[GameEvent],
    ) -> Optional[GMMaturityDecision]:
        recent_events = public_events[-15:]  # 少し多めでもOK
        # Reverse to show newest first
        events_text = format_events_for_maturity(list(reversed(recent_events)))

        prompt = self._build_prompt(events_text=events_text)

        try:
            response = self.llm.generate(
                system=GM_MATURITY_SYSTEM_PROMPT,
                prompt=prompt,
            )
            return response
        except Exception:
            # 成熟判定に失敗したら「未成熟」とみなす
            return GMMaturityDecision(is_mature=False, reason="LLM error fallback")

    def _build_prompt(self, *, events_text: str) -> str:
        return f"""
Recent discussion events:
{events_text}

Your task:
Carefully judge whether the discussion is truly mature.

Remember:
- If there is any doubt, choose is_mature = false
- Do not rush the game forward

Output JSON with:
- is_mature: true or false
- reason: short Japanese GM comment
"""


gm_maturity_judge = GMMaturityJudge(llm=create_gm_maturity_llm())
