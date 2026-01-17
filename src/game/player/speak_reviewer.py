# src/game/player/speak_reviewer.py
from typing import Optional

from src.core.llm.client import LLMClient
from src.core.llm.prompts import SPEAK_REVIEW_SYSTEM_PROMPT
from src.core.memory.strategy import Strategy, SpeakReview
from src.core.memory.speak import Speak
from src.core.types.player import PlayerMemory
from src.config.llm import create_speak_reviewer_llm


class SpeakReviewer:
    """
    生成された発言をレビューするクラス。

    設計方針:
    - 発言が戦略に沿っているかをチェック
    - ゲームルール違反がないか確認
    - 自然な日本語かどうかを確認
    """

    def __init__(self, llm: LLMClient):
        self.llm = llm

    def review(
        self,
        *,
        speak: Speak,
        strategy: Strategy,
        memory: PlayerMemory,
    ) -> Optional[SpeakReview]:
        """
        発言をレビューする。

        失敗した場合は None を返す（安全側に倒す = commit）。
        """
        prompt = self._build_prompt(speak, strategy, memory)

        try:
            result: SpeakReview = self.llm.generate(
                system=SPEAK_REVIEW_SYSTEM_PROMPT,
                prompt=prompt,
            )
            print(f"[SpeakReviewer] Review result: needs_fix={result.needs_fix}")
            print(result)
            return result

        except Exception as e:
            print(f"[SpeakReviewer] Failed to review speak: {e}")
            return None

    def _build_prompt(
        self, speak: Speak, strategy: Strategy, memory: PlayerMemory
    ) -> str:
        """
        レビュー用のプロンプトを構築する。
        """
        self_name = memory.self_name
        
        return f"""
==============================
SPEAKER IDENTITY CHECK
==============================

The speaker is: {self_name}

Check for SELF-REFERENCE violations:
- Does the speech contain "{self_name}さん" or "{self_name}は"? (Your OWN name)
- Does the speech refer to the speaker in third person?
- If YES to any, this is INVALID and needs_fix = true
- NOTE: Using OTHER players' names is CORRECT and NOT a violation.

Check for AMBIGUOUS PRONOUNS:
- Does the speech use "彼", "彼女", "あの人", "そいつ"?
- If YES, this is INVALID and needs_fix = true (must use explicit names).

Player: {self_name}
Role: {memory.self_role}

Strategy this speech should follow:
- Goals: {strategy.goals}
- Approach: {strategy.approach}
- Key Points: {strategy.key_points}

Speech to review:
"{speak.text}"

Review this speech for strategy alignment and self-reference violations.
Output JSON only.
"""


# --- グローバルインスタンス ---
speak_reviewer = SpeakReviewer(llm=create_speak_reviewer_llm())
