# src/game/player/speak_reviewer.py
from typing import Optional

from src.core.llm.client import LLMClient
from src.core.llm.prompts import SPEAK_REVIEW_SYSTEM_PROMPT
from src.core.memory.strategy import Strategy, SpeakReview
from src.core.memory.speak import Speak
from src.core.types.player import PlayerMemory
from src.config.llm import create_speak_reviewer_llm
from src.game.player.belief_utils import build_belief_analysis_section


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
        game_def: "GameDefinition",
    ) -> Optional[SpeakReview]:
        """
        発言をレビューする。

        失敗した場合は None を返す（安全側に倒す = commit）。
        """
        prompt = self._build_prompt(speak, strategy, memory, game_def)

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
        self, speak: Speak, strategy: Strategy, memory: PlayerMemory, game_def: "GameDefinition"
    ) -> str:
        """
        レビュー用のプロンプトを構築する。
        
        設計方針:
        - log_summary: 議論経緯の参照（事実確認用）
        - belief_analysis: 信念との整合性チェック用
        - レビュー責務に必要な情報のみを提供
        """
        self_name = memory.self_name
        
        # 要約済みログを使用（事実確認の単一ソース）
        log_summary = memory.log_summary if memory.log_summary else "(No events summarized yet)"

        # 役職推定分析セクションの構築（整合性チェック用）
        belief_analysis = build_belief_analysis_section(memory, game_def)

        return f"""
==============================
SPEAKER IDENTITY: {self_name}
==============================

Player: {self_name}
Role: {memory.self_role}

==============================
REVIEW CHECKLIST
==============================

1. HALLUCINATIONS (FACTUAL ERRORS) [PRIORITY 1]:
   - Does the speech reference a player/event NOT in the log summary?
   - If YES → needs_fix = true, reason must mention "Hallucination"

2. SELF-REFERENCE VIOLATIONS:
   - Does the speech contain "{self_name}さん" or "{self_name}は"?
   - Does the speech refer to self in third person?
   - If YES → needs_fix = true

3. AMBIGUOUS PRONOUNS:
   - Does the speech use "彼", "彼女", "あの人", "そいつ"?
   - If YES → needs_fix = true (must use explicit names)

4. BELIEF CONTRADICTIONS:
   - Does the speech contradict your beliefs below?
   - If YES → needs_fix = true

5. ROLE-INAPPROPRIATE BEHAVIOR:
   - 占い師: Should share facts, NOT hide results
   - 人狼: Should blend in, NOT expose self
   - 狂人: Should create confusion, NOT help village
   - 村人: Should analyze facts, NOT make false claims
   - If contradicts role incentives → needs_fix = true

==============================
GAME LOG SUMMARY
==============================
{log_summary}

==============================
ROLE BELIEF ANALYSIS
==============================
{belief_analysis}

==============================
STRATEGY ALIGNMENT
==============================
- Action: {strategy.action_type}
- Target: {strategy.target_player or "(None)"}
- Style: {strategy.style_instruction}
- Focus: {strategy.value_focus}

==============================
SPEECH TO REVIEW
==============================
"{speak.text}"

Output JSON only.
"""


# --- グローバルインスタンス ---
speak_reviewer = SpeakReviewer(llm=create_speak_reviewer_llm())
