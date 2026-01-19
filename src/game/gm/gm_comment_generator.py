# src/game/gm/gm_comment_generator.py
from typing import Optional

from src.core.llm.client import LLMClient
from src.core.llm.prompts import GM_COMMENT_SYSTEM_PROMPT
from src.core.memory.gm_comment import GMComment
from src.core.types import PlayerName, GameEvent
from src.config.llm import create_gm_comment_llm





class GMCommentGenerator:
    """
    GM が観測した public_event から
    次の speaker と進行コメントを生成する。
    
    発言者選定ロジック:
    - 基本: シンプルなラウンドロビン（全員が順番に発言）
    - 補助: 直前の発言で名指しされた人がいれば優先
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

        # 発言回数と直前発言者を集計
        speak_counts = {p: 0 for p in players}
        last_speaker = None
        for event in public_events:
            if event.event_type == "speak":
                speaker = event.payload.get("player")
                if speaker in speak_counts:
                    speak_counts[speaker] += 1
                last_speaker = speaker

        # 直近15件だけを見る
        recent_events = public_events[-15:]

        is_opening = (
            len(recent_events) > 0 and recent_events[-1].event_type == "night_started"
        )

        # シンプルな発言者選定
        next_speaker, selection_reason = self._get_next_speaker(
            players=players,
            speak_counts=speak_counts,
            last_speaker=last_speaker,
            recent_events=recent_events,
        )

        prompt = self._build_prompt(
            players=players,
            next_speaker=next_speaker,
            selection_reason=selection_reason,
            is_opening=is_opening,
            speak_counts=speak_counts,
            last_speaker=last_speaker,
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

    def _get_next_speaker(
        self,
        players: list[PlayerName],
        speak_counts: dict[PlayerName, int],
        last_speaker: Optional[PlayerName],
        recent_events: list[GameEvent],
    ) -> tuple[PlayerName, str]:
        """
        シンプルなラウンドロビン + 文脈補助による発言者選定。
        
        Returns:
            tuple: (next_speaker, selection_reason)
        """
        # 1. 未発言者リストを取得（プレイヤー順序を維持）
        unspoken = [p for p in players if speak_counts.get(p, 0) == 0]
        
        # 2. 全員発言済みなら新ラウンド開始
        if not unspoken:
            unspoken = list(players)
        
        # 3. 直前発言者を除外（連続指名防止）
        candidates = [p for p in unspoken if p != last_speaker]
        if not candidates:
            candidates = unspoken
        
        # 4. 文脈ヒント: 直前の発言で名指しされた人がいれば優先
        mentioned = self._get_mentioned_player(recent_events, candidates)
        if mentioned:
            return mentioned, "mentioned_in_last_speech"
        
        # 5. デフォルト: 候補リストの先頭（順番通り）
        return candidates[0], "round_robin"

    def _get_mentioned_player(
        self,
        recent_events: list[GameEvent],
        candidates: list[PlayerName],
    ) -> Optional[PlayerName]:
        """
        直前の発言で名指しされたプレイヤーを候補から探す。
        見つからなければ None を返す。
        """
        if not recent_events:
            return None
        
        # 直前の発言イベントのみを見る
        last_event = recent_events[-1]
        if last_event.event_type != "speak":
            return None
        
        text = last_event.payload.get("text", "")
        speaker = last_event.payload.get("player", "")
        
        # 発言者以外で、テキスト内に名前が含まれる候補を探す
        for p in candidates:
            if p != speaker and p in text:
                return p
        
        return None

    def _build_prompt(
        self,
        *,
        players: list[PlayerName],
        next_speaker: PlayerName,
        selection_reason: str,
        is_opening: bool,
        speak_counts: dict[PlayerName, int],
        last_speaker: Optional[PlayerName],
        log_summary: str = "",
    ) -> str:
        """
        GM 用 user prompt を構築する。
        """
        # 発言状況のフォーマット
        stats_lines = []
        for p in players:
            count = speak_counts.get(p, 0)
            status = "✓" if count > 0 else "未発言"
            stats_lines.append(f"- {p}: {count}回 ({status})")
        stats_text = "\n".join(stats_lines)

        last_speaker_text = f"直前の発言者: {last_speaker}" if last_speaker else "直前の発言者: なし"
        
        # 選定理由のヒント
        if selection_reason == "mentioned_in_last_speech":
            reason_hint = f"（直前の発言で {next_speaker} が言及されました）"
        else:
            reason_hint = "（順番による選定）"

        opening_text = ""
        if is_opening:
            opening_text = """
フェーズ:
- これは議論の最初のGMコメントです
- まだ誰も発言していません
- 主張や疑惑はまだありません
"""

        # ログサマリーセクション
        log_summary_section = ""
        if log_summary:
            log_summary_section = f"""
==============================
ゲームログ要約
==============================
{log_summary}
"""

        return f"""
{opening_text}
{log_summary_section}

発言状況:
{stats_text}

{last_speaker_text}

次の発言者: {next_speaker} {reason_hint}

(直近のイベント詳細はログ要約を参照してください)
"""


# --- グローバルに1つだけ ---
gm_comment_generator = GMCommentGenerator(llm=create_gm_comment_llm())
