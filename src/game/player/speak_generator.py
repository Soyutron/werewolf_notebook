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

    設計原則:
    - Strategy（行動指針）は strategy_generator.py が strategy_plan_generator.py の
      StrategyPlan に基づいて生成したものを入力として受け取る
    - 本クラスは Strategy を忠実に実行する発言を生成する責務のみを持つ
    - 独自に戦略を再解釈・再生成することは禁止
    - belief_analysis は戦略判断のためではなく、発言の具体性向上のための
      参考情報としてのみ使用する

    責務:
    - 発言内容のみを生成する（state は変更しない）
    - Strategy が与えられた場合は、戦略パラメータを忠実に実行する発言を生成する
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

        strategy は strategy_generator.py から渡される行動指針。
        戦略が与えられた場合は、そのパラメータを忠実に実行する発言を生成する。
        戦略なしで呼ばれた場合は警告を出力し、基本的な発言を生成する。
        失敗した場合は None を返す。
        """
        # Strategy が存在しない場合は警告（本来は strategy_generator.py から渡されるべき）
        if strategy is None:
            print(f"[SpeakGenerator] WARNING: No Strategy provided for {memory.self_name}. Generating without strategic guidance.")
        
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

        戦略が与えられた場合は、戦略のパラメータを忠実に実行する発言を生成する。
        co_decision が co_now の場合は CO を強制する。
        
        設計原則:
        - Strategy: 行動指針として最優先で従う（strategy_plan_generator.py → strategy_generator.py 由来）
        - log_summary: 議論経緯と観測結果の要約（発言の具体性向上のため）
        - belief_analysis: 役職推定の参考情報（戦略判断には使用しない）
        """
        # 公開情報の抽出（ターゲット未発言チェック用）
        public_speeches = [
            e for e in memory.observed_events 
            if e.event_type == "speak"
        ]
        
        # 発言済みプレイヤーの集合（ターゲットの発言有無チェック用）
        speakers = {e.payload.get('player') for e in public_speeches if e.payload.get('player')}
        
        # 注意: 独自にフェーズ判定や戦略的推奨を行わない
        # Strategyのパラメータを忠実に実行することに集中する
        # フェーズに応じた戦略判断はstrategy_generator.pyで既に行われている

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
STRATEGY PARAMETERS (EXECUTE THIS - DO NOT REINTERPRET)
==============================

Your action is determined by these parameters. Execute them faithfully.
Do NOT make independent strategic decisions - the strategy has already been decided.

1. [ACTION] Type: {strategy.action_type}
   - Target: {strategy.target_player or "(None)"} {target_warning}
   
2. [TONE & STYLE]
   - Aggression: {strategy.aggression_level}/10 (1=Calm/Polite, 10=Furious/Assertive)
   - Doubt: {strategy.doubt_level}/10 (1=Trusting, 10=Accusing)
   - Focus: {strategy.value_focus} (Make your argument based on this)
   - Instruction: "{strategy.style_instruction}"

3. [GOAL]
   Achieve the action type with the specified tone.
   Generate speech that EXECUTES these parameters.
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
1. EXECUTE the strategy parameters faithfully - do not reinterpret or override them
2. Use the log summary for context to make your speech concrete and relevant
3. Use belief analysis as reference information only (not for strategic decisions)

Generate a public statement that executes the given strategy. Output JSON only.
"""


# --- グローバルに1つだけ ---
speak_generator = SpeakGenerator(llm=create_speak_llm())
