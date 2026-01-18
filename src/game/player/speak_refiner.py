# src/game/player/speak_refiner.py
from typing import Optional

from src.core.llm.client import LLMClient
from src.core.llm.prompts import SPEAK_REFINE_SYSTEM_PROMPT
from src.core.memory.strategy import Strategy, SpeakReview
from src.core.memory.speak import Speak
from src.core.types.player import PlayerMemory
from src.config.llm import create_speak_refiner_llm
from src.game.player.belief_utils import build_belief_analysis_section, get_role_guidance


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
    ) -> Optional[Speak]:
        """
        発言をリファインする。

        失敗した場合は None を返す。
        """
        prompt = self._build_prompt(original, strategy, review, memory)

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
    ) -> str:
        """
        リファイン用のプロンプトを構築する。
        """
        # 自己言及禁止のガード（最上位に配置）
        self_name = memory.self_name
        valid_partners = [p for p in memory.players if p != self_name]
        
        # --- 公開情報の抽出 (SpeakGeneratorと同じロジック) ---
        public_speeches = [
            e for e in memory.observed_events 
            if e.event_type == "speak"
        ]
        speakers = {e.payload.get('player') for e in public_speeches if e.payload.get('player')}
        
        public_history_text = "\n".join(
            f"- {e.payload.get('player')}: {e.payload.get('text')}"
            for e in public_speeches
        )

        # --- Belief分析セクションの構築 ---
        belief_analysis = build_belief_analysis_section(memory)
        role_guidance = get_role_guidance(memory.self_role)

        # ターゲット未発言の警告と戦略の無効化
        target_warning = ""
        strategy_text = f"""
Strategy to follow:
- Goals: {strategy.goals}
- Approach: {strategy.approach}
- Key Points: {strategy.key_points}
"""

        # 戦略のターゲットがまだ発言していない場合（幻覚防止）
        if strategy.primary_target and strategy.primary_target not in speakers:
            target_warning = f"""
!!! WARNING: TARGET '{strategy.primary_target}' HAS NOT SPOKEN !!!
- The Strategy above claims they said something, but they are SILENT.
- The Strategy is BASED ON HALLUCINATION. IGNORE IT.
- NEW GOAL: Simply state that {strategy.primary_target} hasn't spoken yet.
- REMOVE any quotes attributed to them.
"""
            # 戦略テキストを上書きして誤誘導を防ぐ
            strategy_text = f"""
Strategy to follow (MODIFIED SAFE MODE):
- Goals: [Safely question {strategy.primary_target}]
- Approach: {strategy.primary_target} has not spoken. Point this out.
- Key Points: ["{strategy.primary_target} is silent.", "Do not quote them."]
"""

        return f"""
==============================
CRITICAL: YOU ARE {self_name}
==============================

- You are speaking as {self_name}
- Use first-person (私/俺/僕)
- NEVER say "{self_name}さん" or refer to yourself in third person
- NEVER use vague pronouns ("彼", "彼女", "あの人", "そいつ"). ALWAYS use specific names.

Player: {self_name}
Role: {memory.self_role}
Valid Partners: {valid_partners}

{target_warning}
{strategy_text}

==============================
PUBLIC FACTS (CHECK THIS)
==============================
The following is the ONLY objective history.
If a player is not listed here, they have NOT spoken.
{public_history_text if public_history_text else "(No one has spoken)"}

==============================
ROLE BELIEF CONTEXT (FOR CONSISTENCY)
==============================

Your current beliefs about other players:
{belief_analysis}

When refining, ensure:
1. Speech is CONSISTENT with your beliefs
   - If you believe X is 人狼(70%), don't say "X is trustworthy"
   - If you believe X is 占い師(80%), treat their claim with respect
2. Speech is ROLE-APPROPRIATE
   - As {memory.self_role}, you should: {role_guidance}
3. Maintain role-based conviction
   - 人狼: Be careful not to expose yourself or help village
   - 占い師: Be confident about your divination result
   - 狂人: Create confusion, not clarity
   - 村人: Analyze based on facts, don't blindly trust

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
4. Remove any hallucinations (quotes from silent players)

Apply minimal changes otherwise.
Output JSON only.
"""


# --- グローバルインスタンス ---
speak_refiner = SpeakRefiner(llm=create_speak_refiner_llm())
