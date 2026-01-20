# src/game/player/speak_generator.py
from typing import Optional, Union

from src.core.llm.client import LLMClient
from src.core.llm.prompts import SPEAK_SYSTEM_PROMPT
from src.core.memory.speak import Speak
from src.core.memory.strategy import Strategy, PlayerPolicyWeights
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
        game_def: "GameDefinition",
        strategy: Optional[Strategy] = None,
        policy_weights: Optional[PlayerPolicyWeights] = None,
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
        
        prompt = self._build_prompt(memory, observed, game_def, strategy, policy_weights)

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
        game_def: "GameDefinition",
        strategy: Optional[Strategy] = None,
        policy_weights: Optional[PlayerPolicyWeights] = None,
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
        belief_analysis = build_belief_analysis_section(memory, game_def)

        # 要約済みログを使用（議論経緯と観測結果の単一ソース）
        log_summary = memory.log_summary if memory.log_summary else "(No events summarized yet)"

        # 戦略コンテキストの構築
        strategy_section = ""
        
        if strategy is not None:
            # 1. Main Action Interpretation
            main_action = strategy.main_action
            
            # CO Action Special Handling
            if main_action.action_type == "co" and main_action.co_content:
                co = main_action.co_content
                strategy_section += f"""
==============================
MAIN ACTION: CO (MUST EXECUTE)
==============================
You MUST Come Out (CO) in this turn.
- Title: {co.role} CO
- Target: {co.target or "None"}
- Result: {co.result or "decide yourself based on game log"}
- Reason: {co.reason or "strategic necessity"}

Instruction: {main_action.description}
"""
            else:
                strategy_section += f"""
==============================
MAIN ACTION: {main_action.action_type.upper()}
==============================
- Trigger: {main_action.trigger}
- Target: {main_action.target_player or "None"}
- Instruction: {main_action.description}
"""
            
            # 2. Conditional Actions
            if strategy.conditional_actions:
                strategy_section += "\n[CONDITIONAL ACTIONS]\n"
                for i, action in enumerate(strategy.conditional_actions, 1):
                    co_info = f" (CO: {action.co_content.role})" if action.co_content else ""
                    strategy_section += f"{i}. IF [{action.trigger}]: {action.action_type.upper()}{co_info} -> {action.description}\n"

            # 3. Style & Tone
            strategy_section += f"""
==============================
STYLE & TONE
==============================
- Focus: {strategy.style_focus}
- Style Instruction: "{strategy.text_style}"
- Current Priority: "{strategy.current_priority}"
"""
            
            # Target warning (Keep existing logic)
            if main_action.target_player and main_action.target_player not in speakers:
                 strategy_section += f"\n(Note: Target '{main_action.target_player}' has not spoken yet. Adjust your wording to avoid claiming they said something.)\n"

        else:
             strategy_section = "(No Strategy Provided - Act freely based on your role)"

        # policy_weights セクション（マイルストーン状態から算出された重み）
        policy_weights_section = ""
        if policy_weights is not None:
            policy_weights_section = f"""
==============================
発言方針調整パラメータ (参考情報)
==============================

これらの値はゲームの進行状況から動的に算出されたものです。
発言のトーン調整の参考にしてください（戦略パラメータが優先）。

- 攻撃性: {policy_weights.aggression}/10
- 信頼構築: {policy_weights.trust_building}/10
- 情報開示度: {policy_weights.information_reveal}/10
- 緊急度: {policy_weights.urgency}/10
{f"- 注目プレイヤー: {policy_weights.focus_player}" if policy_weights.focus_player else ""}
"""

        # 自己言及禁止のガード
        self_name = memory.self_name
        anti_self_ref_section = f"""
==============================
あなたは {self_name} です
==============================

- 一人称を使ってください（私/俺/僕など）
- 決して「{self_name}さん」と言ったり、自分を三人称で呼ばないでください
"""

        return f"""
{anti_self_ref_section}
{strategy_section}
{policy_weights_section}

==============================
ゲームログ要約
==============================
{log_summary}

==============================
役職推定分析
==============================

他プレイヤーの役職に関するあなたの分析:
{belief_analysis}

発言生成時の注意:
1. 戦略パラメータを誠実に実行してください - 再解釈や無視は禁止です。
2. ログ要約を文脈として使用し、具体的で関連性のある発言にしてください。
3. 役職推定分析は参考情報としてのみ使用してください（戦略的決定には使用しないでください）。

与えられた戦略を実行する公の発言を生成してください。出力はJSONのみです。
"""


# --- グローバルに1つだけ ---
speak_generator = SpeakGenerator(llm=create_speak_llm())
