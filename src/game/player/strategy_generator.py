# src/game/player/strategy_generator.py
from typing import Optional, Dict

from src.core.llm.client import LLMClient
from src.core.llm.prompts import (
    SEER_STRATEGY_SYSTEM_PROMPT,
    WEREWOLF_STRATEGY_SYSTEM_PROMPT,
    MADMAN_STRATEGY_SYSTEM_PROMPT,
    VILLAGER_STRATEGY_SYSTEM_PROMPT,
)
from src.core.memory.strategy import Strategy
from src.core.types.player import PlayerMemory
from src.config.llm import create_strategy_llm

# 役職ごとのプロンプトマッピング
ROLE_STRATEGY_PROMPTS: Dict[str, str] = {
    "seer": SEER_STRATEGY_SYSTEM_PROMPT,
    "werewolf": WEREWOLF_STRATEGY_SYSTEM_PROMPT,
    "madman": MADMAN_STRATEGY_SYSTEM_PROMPT,
    "villager": VILLAGER_STRATEGY_SYSTEM_PROMPT,
}


class StrategyGenerator:
    """
    プレイヤーの発言前戦略を生成するクラス。

    設計方針:
    - 役職ごとに異なるプロンプトを使用
    - 現在のゲーム状況（memory）を考慮した戦略生成
    - 生成のみを担当（state は変更しない）
    """

    def __init__(self, llm: LLMClient):
        self.llm = llm

    def generate(
        self,
        *,
        memory: PlayerMemory,
    ) -> Optional[Strategy]:
        """
        役職に応じた戦略を生成する。

        失敗した場合は None を返す。
        """
        role = memory.self_role
        system_prompt = ROLE_STRATEGY_PROMPTS.get(
            role, VILLAGER_STRATEGY_SYSTEM_PROMPT
        )

        prompt = self._build_prompt(memory)

        try:
            strategy: Strategy = self.llm.generate(
                system=system_prompt,
                prompt=prompt,
            )
            print(f"[StrategyGenerator] Generated strategy for {memory.self_name}")
            print(strategy)
            return strategy

        except Exception as e:
            print(f"[StrategyGenerator] Failed to generate strategy: {e}")
            return None

    def _contains_co_statement(self, text: str) -> bool:
        """
        発言テキストにCO表現が含まれるか判定する。
        """
        co_patterns = [
            "私は占い師",
            "占い師です",
            "COします",
            "カミングアウト",
            "占い師CO",
            "人狼CO",
            "狂人CO",
            "村人CO",
            "占った結果",
            "占いました",
            "結果は人狼",
            "結果は村人",
        ]
        return any(pattern in text for pattern in co_patterns)
    
    def _detect_own_co(self, memory: PlayerMemory) -> tuple[bool, str]:
        """
        自分がすでにCOしたかどうかを検出する。
        
        Returns:
            tuple[bool, str]: (CO済みかどうか, CO内容の要約)
        """
        own_co_statements = []
        for event in memory.observed_events:
            if event.event_type == "speak":
                speaker = event.payload.get("player", "")
                text = event.payload.get("text", "")
                if speaker == memory.self_name and self._contains_co_statement(text):
                    own_co_statements.append(text)
        
        if own_co_statements:
            return True, own_co_statements[-1]  # 最新のCO発言を返す
        return False, ""

    def _build_prompt(self, memory: PlayerMemory) -> str:
        """
        戦略生成用のプロンプトを構築する。
        """
        role_beliefs_text = "\n".join(
            f"- {player}: {belief.probs}"
            for player, belief in memory.role_beliefs.items()
        )

        recent_history = memory.history[-10:]
        history_text = "\n".join(
            f"- [{h.kind}] {h.text if hasattr(h, 'text') else str(h)}"
            for h in reversed(recent_history)
        )

        observed_events_text = "\n".join(
            f"- {e.event_type}: {e.payload}"
            for e in reversed(memory.observed_events[-10:])
        )

        # CO済み検出
        has_already_co, last_co_text = self._detect_own_co(memory)
        
        # POST-CO 強制セクション
        post_co_enforcement = ""
        if has_already_co:
            post_co_enforcement = f"""
==============================
⚠️ CRITICAL: YOU HAVE ALREADY CO'd!
==============================

Your previous CO statement:
「{last_co_text[:100]}{'...' if len(last_co_text) > 100 else ''}」

The village ALREADY KNOWS your claim. DO NOT REPEAT IT.

🚫 BANNED:
- action_type = "co" (YOU ALREADY DID THIS)
- co_decision = "co_now" (SET TO null OR "no_co")
- Repeating "私は占い師です" or similar

✅ REQUIRED FOCUS:
- action_type = "vote_inducement" → Push for a vote on your target
- action_type = "analysis" → Point out contradictions, refute counter-claims
- action_type = "question" → Press suspicious players for answers

Your job NOW is to:
1. DEFEND your CO against challengers
2. ATTACK those who contradict you
3. CONVINCE villagers to VOTE with you

DO NOT waste time restating known facts.
"""

        # 占い師の場合、占い結果を明示的に抽出
        divine_result_section = ""
        if memory.self_role == "seer":
            for event in memory.observed_events:
                if event.event_type == "divine_result":
                    # CO済みの場合は「すでに公開済み」と明記
                    if has_already_co:
                        divine_result_section = f"""
==============================
YOUR DIVINATION RESULT (ALREADY PUBLIC)
==============================

You divined: {event.payload.get('target', 'unknown')}
Result: {event.payload.get('result', 'unknown')}

⚠️ You have ALREADY shared this. Do not repeat the CO.
Focus on defending your claim or attacking rivals.
"""
                    else:
                        divine_result_section = f"""
==============================
YOUR DIVINATION RESULT (CRITICAL)
==============================

You divined: {event.payload.get('target', 'unknown')}
Result: {event.payload.get('result', 'unknown')}

This is CONFIRMED TRUTH. Use it in your strategy.
If you decide to CO (co_decision = "co_now"), set:
- co_target = "{event.payload.get('target', '')}"
- co_result = "{event.payload.get('result', '')}"
"""
                    break

        return f"""
You are {memory.self_name}.
Your role is: {memory.self_role}

Players in this game: {', '.join(memory.players)}
{post_co_enforcement}
{divine_result_section}
Recent game events:
{observed_events_text if observed_events_text else "(none yet)"}

Your current beliefs about other players:
{role_beliefs_text if role_beliefs_text else "(no beliefs formed yet)"}

Your recent internal thoughts:
{history_text if history_text else "(none yet)"}

Generate a strategy for your next public statement.
Output JSON only.
"""


# --- グローバルインスタンス ---
strategy_generator = StrategyGenerator(llm=create_strategy_llm())
