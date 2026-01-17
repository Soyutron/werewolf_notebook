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
            for h in recent_history
        )

        observed_events_text = "\n".join(
            f"- {e.event_type}: {e.payload}"
            for e in memory.observed_events[-10:]
        )

        return f"""
You are {memory.self_name}.
Your role is: {memory.self_role}

Players in this game: {', '.join(memory.players)}

Recent game events:
{observed_events_text if observed_events_text else "(none yet)"}

Your current beliefs about other players:
{role_beliefs_text if role_beliefs_text else "(no beliefs formed yet)"}

Your recent internal thoughts:
{history_text if history_text else "(none yet)"}

Based on this situation, generate a strategy for your next public statement.
Output JSON only.
"""


# --- グローバルインスタンス ---
strategy_generator = StrategyGenerator(llm=create_strategy_llm())
