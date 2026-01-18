# src/game/gm/gm_comment_generator.py
from typing import Optional
import random

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

        # Speak counts and last speaker logic
        speak_counts = {p: 0 for p in players}
        last_speaker = None
        for event in public_events:
            if event.event_type == "speak":
                speaker = event.payload.get("player")
                if speaker in speak_counts:
                    speak_counts[speaker] += 1
                last_speaker = speaker

        # ★ 直近15件だけを見る
        recent_events = public_events[-15:]
        events_text = format_events_for_gm(list(reversed(recent_events)))

        is_opening = (
            len(recent_events) > 0 and recent_events[-1].event_type == "night_started"
        )

        # Prevent consecutive nomination
        # However, if there are only 2 players (rare in OneNight, but possible in testing),
        # strictly banning the last speaker forces a ping-pong which is fine.
        # But if there's only 1 player? Unlikely.
        # General rule: Create a list of Valid Next Speakers.
        
        candidates = []
        if last_speaker and len(players) > 1:
            candidates = [p for p in players if p != last_speaker]
        else:
            candidates = list(players)

        prompt = self._build_prompt(
            events_text=events_text,
            players=players,
            candidates=candidates,
            is_opening=is_opening,
            speak_counts=speak_counts,
            last_speaker=last_speaker,
        )

        try:
            response = self.llm.generate(
                system=GM_COMMENT_SYSTEM_PROMPT,
                prompt=prompt,
            )
            print(response)
            print(response)
            
            # Additional validation: Enforce candidate constraints
            if response and response.speaker not in candidates and candidates:
                print(f"GM Warning: LLM selected invalid speaker {response.speaker}. Overriding with random candidate.")
                response.speaker = random.choice(candidates)
                # Note: The text might still address the invalid speaker, but preventing the loop is prioritized.
            
            return response
        except Exception:
            # GMコメント生成に失敗しても進行は止めない
            return None

    def _build_prompt(
        self,
        *,
        events_text: str,
        players: list[PlayerName],
        candidates: list[PlayerName],
        is_opening: bool,
        speak_counts: dict[PlayerName, int],
        last_speaker: Optional[PlayerName],
    ) -> str:
        """
        GM 用 user prompt を構築する。
        """
        # Format speaking stats
        stats_lines = []
        for p in players:
            count = speak_counts.get(p, 0)
            stats_lines.append(f"- {p}: {count}回")
        stats_text = "\n".join(stats_lines)

        last_speaker_text = f"Last Speaker: {last_speaker}" if last_speaker else "Last Speaker: None"
        
        candidates_text = ", ".join(candidates)
        candidates_section = f"Candidate Speakers (You MUST choose from here): {candidates_text}"

        opening_text = ""
        if is_opening:
            opening_text = """
Phase:
- This is the FIRST GM comment of the discussion.
- No player has spoken yet.
- There are no accusations or opinions yet.
"""

        return f"""
{opening_text}

Player Status:
{stats_text}

{last_speaker_text}
{candidates_section}

Recent public events:
{events_text}
"""


# --- グローバルに1つだけ ---
gm_comment_generator = GMCommentGenerator(llm=create_gm_comment_llm())
