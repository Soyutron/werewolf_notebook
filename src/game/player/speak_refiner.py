# src/game/player/speak_refiner.py
from typing import Optional

from src.core.llm.client import LLMClient
from src.core.llm.prompts import SPEAK_REFINE_SYSTEM_PROMPT
from src.core.memory.strategy import Strategy, SpeakReview
from src.core.memory.speak import Speak
from src.core.types.player import PlayerMemory
from src.config.llm import create_speak_refiner_llm
from src.game.player.belief_utils import build_belief_analysis_section


class SpeakRefiner:
    """
    レビュー指摘を反映して発言を修正するクラス。

    設計方針:
    - 最小限の変更で修正を行う
    - 戦略の key_points に沿った内容を維持
    - 自然な日本語を維持
    """

    def __init__(self, llm: LLMClient):
        self.llm = llm

    def refine(
        self,
        *,
        original: Speak,
        strategy: Strategy,
        review: SpeakReview,
        memory: PlayerMemory,
        game_def: "GameDefinition",
    ) -> Optional[Speak]:
        """
        発言をリファインする。

        失敗した場合は None を返す。
        """
        prompt = self._build_prompt(original, strategy, review, memory, game_def)

        try:
            refined: Speak = self.llm.generate(
                system=SPEAK_REFINE_SYSTEM_PROMPT,
                prompt=prompt,
            )
            print(f"[SpeakRefiner] Refined speech for {memory.self_name}")
            print(refined)
            return refined

        except Exception as e:
            print(f"[SpeakRefiner] Failed to refine speech: {e}")
            return None

    def _build_prompt(
        self,
        original: Speak,
        strategy: Strategy,
        review: SpeakReview,
        memory: PlayerMemory,
        game_def: "GameDefinition",
    ) -> str:
        """
        リファイン用のプロンプトを構築する。
        
        設計方針:
        - log_summary: 議論経緯の参照（事実確認用）
        - belief_analysis: 信念との整合性確保用
        - review feedback: 修正指示の単一ソース
        - ターゲット未発言チェックのみ individual check を維持
        """
        self_name = memory.self_name
        valid_partners = [p for p in memory.players if p != self_name]
        
        # ターゲット未発言チェック用に発言者を抽出
        public_speeches = [
            e for e in memory.observed_events 
            if e.event_type == "speak"
        ]
        speakers = {e.payload.get('player') for e in public_speeches if e.payload.get('player')}

        # 要約済みログを使用（事実確認の単一ソース）
        log_summary = memory.log_summary if memory.log_summary else "(No events summarized yet)"

        # 役職推定分析セクションの構築（整合性確保用）
        belief_analysis = build_belief_analysis_section(memory, game_def)

        # ターゲット未発言の警告と戦略の無効化
        target_warning = ""
        strategy_text = f"""
- Action: {strategy.action_type}
- Target: {strategy.target_player or "(None)"}
- Style: {strategy.style_instruction}
- Focus: {strategy.value_focus}
"""

        # 戦略のターゲットがまだ発言していない場合（幻覚防止）
        if strategy.target_player and strategy.target_player not in speakers:
            target_warning = f"""
!!! WARNING: TARGET '{strategy.target_player}' HAS NOT SPOKEN !!!
- REMOVE any quotes attributed to them.
- NEW GOAL: Point out that {strategy.target_player} hasn't spoken yet.
"""
            strategy_text = f"""
- Action: Question Silence
- Target: {strategy.target_player}
- Instruction: Point out their silence carefully.
"""

        return f"""
==============================
YOU ARE {self_name}
==============================

- Use first-person (私/俺/僕)
- NEVER say "{self_name}さん" or refer to yourself in third person
- NEVER use vague pronouns ("彼", "彼女", "あの人", "そいつ")

Player: {self_name}
Role: {memory.self_role}
Valid Partners: {valid_partners}

==============================
STRATEGY
==============================
{target_warning}
{strategy_text}

==============================
GAME LOG SUMMARY
==============================
{log_summary}

==============================
ROLE BELIEF ANALYSIS
==============================
{belief_analysis}

==============================
REFINEMENT TASK
==============================

Original Speech:
"{original.text}"

Review Feedback:
- Reason: {review.reason}
- Fix Instruction: {review.fix_instruction}

Refine the speech to:
1. Address the fix instruction
2. Maintain belief consistency
3. Ensure role-appropriate behavior
4. Remove any hallucinations

Apply minimal changes otherwise.
Output JSON only.
"""


# --- グローバルインスタンス ---
speak_refiner = SpeakRefiner(llm=create_speak_refiner_llm())
