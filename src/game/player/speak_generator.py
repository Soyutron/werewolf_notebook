# src/game/player/speak_generator.py
from typing import Optional, Union

from src.core.llm.client import LLMClient
from src.core.llm.prompts import SPEAK_SYSTEM_PROMPT
from src.core.memory.speak import Speak
from src.core.memory.strategy import Strategy
from src.core.types import PlayerMemory, GameEvent, PlayerRequest
from src.config.llm import create_speak_llm

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
        """
        observed_type = observed.__class__.__name__

        # 公開情報の抽出と整理
        public_speeches = [
            e for e in memory.observed_events 
            if e.event_type == "speak"
        ]
        
        # 発言済みプレイヤーの集合（ターゲット未発言チェック用）
        speakers = {e.payload.get('player') for e in public_speeches if e.payload.get('player')}
        
        # 議論開始直後かどうかの判定（発言数が少ない場合）
        # 設定: 他者の発言が2つ未満なら「序盤」とみなす
        is_early_game = len(public_speeches) < 2
        
        public_history_text = "\n".join(
            f"- {e.payload.get('player')}: {e.payload.get('text')}"
            for e in public_speeches
        )
        
        # 状況に応じた追加指示
        phase_instruction = ""
        if is_early_game:
            phase_instruction = """
==============================
PHASE: EARLY GAME (Discussion just started)
==============================
- There is NOT enough information to find contradictions yet.
- DO NOT claim "inconsistency" or "logic error" in others unless you can quote 2 conflicting statements.
- Recommended actions:
    - Ask a question (e.g., "Who is the Seer?")
    - State your own role clearly (if beneficial)
    - Prompt others to speak
- AVOID: "His logic is weird" (Too early for this)
"""
        else:
            phase_instruction = """
==============================
PHASE: MID/LATE GAME
==============================
- Compare statements to find contradictions.
- If you find a logical conflict, ATTACK it.
"""

        role_beliefs_text = "\n".join(
            f"- {player}: {belief.probs}"
            for player, belief in memory.role_beliefs.items()
        )

        recent_reflections_list = memory.history[-10:]
        recent_reflections = "\n".join(
            str(r) for r in reversed(recent_reflections_list)
        )

        # 戦略コンテキストの構築
        strategy_section = ""
        co_enforcement_section = ""
        
        if strategy is not None:
            # CO強制セクション（co_now の場合）

            if strategy.co_decision == "co_now":
                # Check for unknown result
                result_instruction = f"3. Result: {strategy.co_result}"
                example_sentence = f"「私は占い師です。昨晩、{strategy.co_target}さんを占いました。結果は{strategy.co_result}でした。皆さんの意見をお聞かせください。」"
                
                if not strategy.co_result or strategy.co_result.lower() == "unknown":
                    result_instruction = "3. Result: Decide a result (White or Black) YOURSELF based on your game plan."
                    example_sentence = f"「私は占い師です。昨晩、{strategy.co_target}さんを占いました。{strategy.co_target}さんは[人狼/村人]でした。皆さん、この情報を踏まえてどう思いますか？」"

                co_enforcement_section = f"""
==============================
MANDATORY CO (YOU MUST DO THIS)
==============================

Your strategy requires you to CO (Come Out) NOW.

Your speech MUST include ALL of the following:
1. 「私は占い師です」or equivalent CO statement
2. Target: {strategy.co_target}
{result_instruction}

Example format:
{example_sentence}

IMPORTANT STYLE RULES:
- Report calmly and factually, like a real Seer would.
- DO NOT use exclamation marks (！).
- DO NOT use interrogative accusations (e.g., 一体何を企んでいるんだ？).
- DO NOT be overly dramatic or emotional.

DO NOT skip the CO. DO NOT hint. STATE IT CLEARLY but CALMLY.
"""
            
            # ターゲットが未発言かどうかのチェック
            target_warning = ""
            if strategy.primary_target and strategy.primary_target not in speakers:
                target_warning = f"""
!!! WARNING: TARGET '{strategy.primary_target}' HAS NOT SPOKEN !!!
- You CANNOT claim they said something.
- You CANNOT find contradictions in their speech.
- You CAN only ask them to speak or question their silence.
- IGNORE any strategy instruction that implies they spoke.
"""

            strategy_section = f"""
==============================
STRATEGY TO FOLLOW
==============================

Action Stance: {strategy.action_stance}
Main Claim: {strategy.main_claim}
Primary Target: {strategy.primary_target or "(none)"}
{target_warning}
Goals:
{chr(10).join(f"- {goal}" for goal in strategy.goals)}

Approach:
{strategy.approach}

Key Points:
{chr(10).join(f"- {point}" for point in strategy.key_points)}
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
PUBLIC FACTS (What everyone knows)
==============================
The following is the ONLY objective history. 
- If an event is NOT listed below, IT DID NOT HAPPEN.
- You CANNOT quote a player who is not in this list.
- If your Strategy says "Refute A", but A is not here, then A did not speak. In that case, IGNORE the strategy's specific instruction and just say "A is silent".
{public_history_text if public_history_text else "(No one has spoken yet)"}

==============================
YOUR PRIVATE BELIEFS (Hidden)
==============================
These are your internal thoughts. Do NOT treat them as public facts.
{role_beliefs_text}

Recent thoughts:
{recent_reflections}

Recent observation:
Type: {observed_type}
Details: {observed.model_dump()}

Generate a public statement. Output JSON only.
"""


# --- グローバルに1つだけ ---
speak_generator = SpeakGenerator(llm=create_speak_llm())
