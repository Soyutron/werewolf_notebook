# src/game/gm/gm_comment_generator.py
from typing import Optional

from src.core.llm.client import LLMClient
from src.core.llm.prompts import GM_COMMENT_SYSTEM_PROMPT
from src.core.memory.gm_comment import GMComment
from src.core.types import PlayerName, GameEvent
from src.config.llm import create_gm_comment_llm


def format_events_for_gm(events: list[GameEvent]) -> str:
    """
    GM が観測した出来事を LLM 向けテキストに整形する。
    """
    return "\n".join(f"- [{e.event_type}] {e.payload}" for e in events)


class GMCommentGenerator:
    """
    GM が観測した public_event から
    次の speaker と進行コメントを生成する。
    """

    def __init__(self, llm: LLMClient):
        self.llm = llm

    def generate(
        self,
        *,
        public_events: list[GameEvent],
        players: list[PlayerName],
    ) -> Optional[GMComment]:
        """
        直近の public_event をもとに GM コメントを生成する。
        """

        # ★ 直近10件だけを見る
        recent_events = public_events[-10:]

        events_text = format_events_for_gm(recent_events)

        prompt = self._build_prompt(
            events_text=events_text,
            players=players,
        )

        try:
            response = self.llm.generate(
                system=GM_COMMENT_SYSTEM_PROMPT,
                prompt=prompt,
            )
            print(response)
            return response
        except Exception:
            # GMコメント生成に失敗しても進行は止めない
            return None

    def _build_prompt(
        self,
        *,
        events_text: str,
        players: list[PlayerName],
    ) -> str:
        """
        GM 用 user prompt を構築する。
        """
        players_text = ", ".join(players)

        return f"""
You are the Game Master.

Players:
{players_text}

Recent public events:
{events_text}

Your task:
- Organize the discussion flow briefly
- Choose exactly ONE next speaker from players
- Invite them to speak
- Write the GM comment in JAPANESE

Output JSON with:
- speaker
- text
"""


# --- グローバルに1つだけ ---
gm_comment_generator = GMCommentGenerator(llm=create_gm_comment_llm())
