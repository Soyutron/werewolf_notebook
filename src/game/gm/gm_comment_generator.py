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
        log_summary: str = "",
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

        # === Fair Speaker Selection Logic ===
        # 1. Identify players who haven't spoken yet
        unspoken_players = [p for p in players if speak_counts[p] == 0]
        all_have_spoken = len(unspoken_players) == 0
        
        # 2. Detect contextual relevance (e.g., question targets from recent events)
        contextual_targets = self._extract_contextual_targets(recent_events, players)
        
        # 3. Build candidate list with priority:
        #    - If not everyone has spoken: only unspoken players are candidates
        #    - If everyone has spoken: reset and allow all players
        #    - Always exclude last speaker to prevent consecutive nomination
        
        if all_have_spoken:
            # Reset: everyone can be nominated again
            base_candidates = list(players)
        else:
            # Prioritize unspoken players exclusively
            base_candidates = unspoken_players
        
        # Exclude last speaker to prevent consecutive nomination
        if last_speaker and len(base_candidates) > 1:
            candidates = [p for p in base_candidates if p != last_speaker]
        else:
            candidates = base_candidates
        
        # If no valid candidates (edge case), fall back to all players except last speaker
        if not candidates:
            candidates = [p for p in players if p != last_speaker] or list(players)
        
        # 4. Among candidates, identify contextually preferred speakers
        preferred_candidates = [p for p in candidates if p in contextual_targets]

        prompt = self._build_prompt(
            events_text=events_text,
            players=players,
            candidates=candidates,
            preferred_candidates=preferred_candidates,
            is_opening=is_opening,
            speak_counts=speak_counts,
            last_speaker=last_speaker,
            all_have_spoken=all_have_spoken,
            log_summary=log_summary,
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
    
    def _extract_contextual_targets(
        self,
        recent_events: list[GameEvent],
        players: list[PlayerName],
    ) -> set[PlayerName]:
        """
        直近のイベントから文脈的に指名されるべきプレイヤーを抽出する。
        例: 質問された相手、言及された相手など
        """
        targets = set()
        
        for event in reversed(recent_events):
            if event.event_type == "speak":
                payload = event.payload
                text = payload.get("text", "")
                speaker = payload.get("player", "")
                
                # Look for mentions of other players in the speech
                for p in players:
                    if p != speaker and p in text:
                        targets.add(p)
                
                # Limit extraction to most recent relevant events
                if len(targets) >= 3:
                    break
        
        return targets

    def _build_prompt(
        self,
        *,
        events_text: str,
        players: list[PlayerName],
        candidates: list[PlayerName],
        preferred_candidates: list[PlayerName],
        is_opening: bool,
        speak_counts: dict[PlayerName, int],
        last_speaker: Optional[PlayerName],
        all_have_spoken: bool,
        log_summary: str = "",
    ) -> str:
        """
        GM 用 user prompt を構築する。
        """
        # Format speaking stats
        stats_lines = []
        for p in players:
            count = speak_counts.get(p, 0)
            status = "✓" if count > 0 else "未発言"
            stats_lines.append(f"- {p}: {count}回 ({status})")
        stats_text = "\n".join(stats_lines)

        last_speaker_text = f"Last Speaker: {last_speaker}" if last_speaker else "Last Speaker: None"
        
        candidates_text = ", ".join(candidates)
        candidates_section = f"Candidate Speakers (You MUST choose from here): {candidates_text}"
        
        # Fairness round status
        if all_have_spoken:
            fairness_status = "Round Status: All players have spoken at least once. New round begins - focus on advancing discussion."
        else:
            unspoken_count = len([p for p in players if speak_counts.get(p, 0) == 0])
            fairness_status = f"Round Status: {unspoken_count} player(s) have NOT spoken yet. PRIORITIZE unspoken players."
        
        # Preferred candidates hint
        preferred_section = ""
        if preferred_candidates:
            preferred_text = ", ".join(preferred_candidates)
            preferred_section = f"\nContextually Preferred (mentioned/questioned in recent discussion): {preferred_text}"

        opening_text = ""
        if is_opening:
            opening_text = """
Phase:
- This is the FIRST GM comment of the discussion.
- No player has spoken yet.
- There are no accusations or opinions yet.
"""

        # Log summary section
        log_summary_section = ""
        if log_summary:
            log_summary_section = f"""
==============================
GAME LOG SUMMARY
==============================
{log_summary}
"""

        return f"""
{opening_text}
{log_summary_section}

Player Status:
{stats_text}

{fairness_status}

{last_speaker_text}
{candidates_section}{preferred_section}

Recent public events:
{events_text}
"""


# --- グローバルに1つだけ ---
gm_comment_generator = GMCommentGenerator(llm=create_gm_comment_llm())
