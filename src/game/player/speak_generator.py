# src/game/player/speak_generator.py
from typing import Optional, Union

from src.core.llm.client import LLMClient
from src.core.llm.prompts import SPEAK_SYSTEM_PROMPT
from src.core.memory.speak import Speak
from src.core.memory.strategy import Strategy
from src.core.types import PlayerMemory, GameEvent, PlayerRequest
from src.config.llm import create_speak_llm
from src.game.player.belief_utils import build_belief_analysis_section

Observed = Union[GameEvent, PlayerRequest]


class SpeakGenerator:
    """
    PlayerMemory と新しく観測した GameEvent / PlayerRequest から
    公開発言（Speak）を生成するクラス。

    設計方針:
    - 発言内容のみを生成する（state は変更しない）
    - 戦略（Strategy）が与えられた場合は、戦略に従った発言を生成する
    - 内省（Reflection）とは責務を分離
    - LLM が失敗しても None を返す
    """

    def __init__(self, llm: LLMClient):
        self.llm = llm

    def generate(
        self,
        *,
        memory: PlayerMemory,
        observed: Observed,
        strategy: Optional[Strategy] = None,
    ) -> Optional[Speak]:
        """
        発言を1件生成する。

        strategy が与えられた場合は、戦略に従った発言を生成する。
        失敗した場合は None を返す。
        """
        prompt = self._build_prompt(memory, observed, strategy)

        try:
            speak: Speak = self.llm.generate(
                system=SPEAK_SYSTEM_PROMPT,
                prompt=prompt,
            )

            print(speak)

            return speak

        except Exception:
            # 発言生成に失敗してもゲーム進行は止めない
            return None

    def _build_prompt(
        self,
        memory: PlayerMemory,
        observed: Observed,
        strategy: Optional[Strategy] = None,
    ) -> str:
        """
        発言生成用の user prompt を構築する。

        戦略が与えられた場合は、戦略のコンテキストをプロンプトに含める。
        co_decision が co_now の場合は CO を強制する。
        
        設計方針:
        - log_summary: 議論経緯と観測結果の要約（重複回避のため単一ソース）
        - belief_analysis: 役職推定の分析情報（推論用に整形済み）
        - 上記2つのみを使用し、同一情報の重複提供を避ける
        """
        # 公開情報の抽出（ターゲット未発言チェック用）
        public_speeches = [
            e for e in memory.observed_events 
            if e.event_type == "speak"
        ]
        
        # 発言済みプレイヤーの集合
        speakers = {e.payload.get('player') for e in public_speeches if e.payload.get('player')}
        
        # 議論開始直後かどうかの判定（発言数が少ない場合）
        is_early_game = len(public_speeches) < 2
        
        # 状況に応じた追加指示
        phase_instruction = ""
        if is_early_game:
            phase_instruction = """
==============================
PHASE: EARLY GAME (Discussion just started)
==============================
- There is NOT enough information to find contradictions yet.
- Recommended actions:
    - Ask a question
    - State your own role clearly (if beneficial)
    - Prompt others to speak
"""
        else:
            phase_instruction = """
==============================
PHASE: MID/LATE GAME
==============================
- Compare statements to find contradictions.
- If you find a logical conflict, ATTACK it.
"""

        # 役職推定分析セクションの構築（推論用に整形済み）
        belief_analysis = build_belief_analysis_section(memory)

        # 要約済みログを使用（議論経緯と観測結果の単一ソース）
        log_summary = memory.log_summary if memory.log_summary else "(No events summarized yet)"

        # 戦略コンテキストの構築
        strategy_section = ""
        co_enforcement_section = ""
        
        if strategy is not None:
            # CO強制セクション（co_now の場合）

            if strategy.co_decision == "co_now":
                # Check for unknown result
                result_instruction = f"3. Result: {strategy.co_result}"
                
                if not strategy.co_result or strategy.co_result.lower() == "unknown":
                    result_instruction = "3. Result: Decide a result (White or Black) YOURSELF based on your game plan."

                co_enforcement_section = f"""
==============================
MANDATORY CO (YOU MUST DO THIS)
==============================

Your strategy requires you to CO (Come Out) NOW.

Your speech MUST include ALL of the following:
1. 「私は占い師です」or equivalent CO statement
2. Target: {strategy.co_target}
{result_instruction}



IMPORTANT STYLE RULES:
- Report calmly and factually.
- DO NOT use exclamation marks.
- DO NOT use interrogative accusations.
- DO NOT be overly dramatic or emotional.

DO NOT skip the CO. DO NOT hint. STATE IT CLEARLY but CALMLY.
"""
            
            # ターゲットが未発言かどうかのチェック
            target_warning = ""
            if strategy.target_player and strategy.target_player not in speakers:
                target_warning = f"""
!!! WARNING: TARGET '{strategy.target_player}' HAS NOT SPOKEN !!!
- You CANNOT claim they said something.
- You CANNOT find contradictions in their speech.
- You CAN only ask them to speak or question their silence.
- IGNORE any strategy instruction that implies they spoke.
"""

            strategy_section = f"""
==============================
STRATEGY PARAMETERS (EXECUTE THIS)
==============================

You must generate speech based on these parameters:

1. [ACTION] Type: {strategy.action_type}
   - Target: {strategy.target_player or "(None)"} {target_warning}
   
2. [TONE & STYLE]
   - Aggression: {strategy.aggression_level}/10 (1=Calm/Polite, 10=Furious/Assertive)
   - Doubt: {strategy.doubt_level}/10 (1=Trusting, 10=Accusing)
   - Focus: {strategy.value_focus} (Make your argument based on this)
   - Instruction: "{strategy.style_instruction}"

3. [GOAL]
   Achieve the action type with the specified tone.
"""

        # 自己言及禁止のガード
        self_name = memory.self_name
        anti_self_ref_section = f"""
==============================
YOU ARE {self_name}
==============================

- Use first-person (私/俺/僕)
- NEVER say "{self_name}さん" or refer to yourself in third person
"""

        return f"""
{anti_self_ref_section}
{co_enforcement_section}
{strategy_section}
{phase_instruction}

==============================
GAME LOG SUMMARY
==============================
{log_summary}

==============================
ROLE BELIEF ANALYSIS
==============================

Your analysis of other players' likely roles:
{belief_analysis}

When generating your speech:
1. Refer to the log summary for discussion context and observations
2. Use the belief analysis to inform your strategic reasoning
3. Generate speech consistent with your strategy parameters

Generate a public statement. Output JSON only.
"""


# --- グローバルに1つだけ ---
speak_generator = SpeakGenerator(llm=create_speak_llm())
