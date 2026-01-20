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
                result_instruction = f"3. 結果: {strategy.co_result}"
                
                if not strategy.co_result or strategy.co_result.lower() == "unknown":
                    result_instruction = "3. 結果: あなたのゲームプランに基づいて、結果（白か黒か）を自分自身で決定してください。"

                co_enforcement_section = f"""
==============================
CO強制 (必ず実行してください)
==============================

あなたの戦略は、今すぐCO（カミングアウト）することを要求しています。

あなたの発言には、以下のすべてを必ず含めてください:
1. 「私は占い師です」または同等のCO発言
2. ターゲット: {strategy.co_target}
{result_instruction}



重要なスタイルルール:
- 冷静かつ事実に基づいて報告してください。
- 感嘆符（！）を多用しないでください。
- 尋問調や攻撃的な口調を避けてください。
- 過度にドラマチックにしないでください。

COをスキップしないでください。匂わせるだけにしないでください。冷静に、しかし明確に宣言してください。
"""
            
            # ターゲットが未発言かどうかのチェック
            target_warning = ""
            if strategy.target_player and strategy.target_player not in speakers:
                target_warning = f"""
!!! 警告: ターゲット '{strategy.target_player}' はまだ発言していません !!!
- 彼らが何か言ったと主張することはできません。
- 彼らの発言の矛盾を指摘することはできません。
- 彼らに発言を求めたり、沈黙を怪しむことしかできません。
- 彼らが発言したことを前提とする戦略指示は無視してください。
"""

            strategy_section = f"""
==============================
戦略パラメータ (これを実行してください - 再解釈禁止)
==============================

あなたの行動はこれらのパラメータによって決定されます。誠実に実行してください。
独自の戦略的決定を行わないでください - 戦略はすでに決定されています。

1. [行動] タイプ: {strategy.action_type}
   - ターゲット: {strategy.target_player or "(なし)"} {target_warning}
   
2. [トーンとスタイル]
   - 積極性: {strategy.aggression_level}/10 (1=冷静/丁寧, 10=激昂/断定的)
   - 疑念度: {strategy.doubt_level}/10 (1=信頼している, 10=強く疑っている)
   - 焦点: {strategy.value_focus} (これに基づいて議論を組み立ててください)
   - 指示: "{strategy.style_instruction}"

3. [目標]
   指定されたトーンで、行動タイプを達成してください。
   これらのパラメータを実行するような発言を生成してください。
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
{co_enforcement_section}
{strategy_section}

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
