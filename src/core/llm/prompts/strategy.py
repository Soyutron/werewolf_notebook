from .base import ONE_NIGHT_WEREWOLF_RULES
from .roles import get_role_description

# =============================================================================
# STRATEGY GENERATION PROMPTS
# =============================================================================
#
# 設計原則:
# - System Prompt: 戦略生成の目的と出力フォーマット
# - Runtime Prompt で提供すべきもの:
#   - 現在のゲーム状況
#   - 他プレイヤーの発言履歴
#   - Belief 情報
# =============================================================================

COMMON_STRATEGY_OUTPUT_FORMAT = """
{
  "co_decision": "co_now" | "co_later" | "no_co" | null,
  "co_target": "プレイヤー名 または null",
  "co_result": "人狼" | "村人" | null,
  "target_player": "プレイヤー名 または null",
  "value_focus": "logic" | "emotion" | "trust" | "aggression",
  "aggression_level": 1-10 (整数),
  "doubt_level": 1-10 (整数),
  "action_type": "co" | "agree" | "disagree" | "question" | "vote_inducement" | "skip",
  "style_instruction": "短いスタイルの指針"
}
"""


# =============================================================================
# DYNAMIC STRATEGY PROMPT GENERATOR
# =============================================================================

def get_strategy_system_prompt(role: str) -> str:
    """
    指定された役職に対応する戦略生成用システムプロンプトを返す。
    
    Args:
        role: 役職名 (villager, seer, werewolf, madman)
    
    Returns:
        役職固有の戦略システムプロンプト
    """
    role_description = get_role_description(role)
    
    return f"""\\
あなたはワンナイト人狼の「行動指針 (Action Guideline)」を作成するAIです。
{ONE_NIGHT_WEREWOLF_RULES}

## 役職
{role_description}

## 設計原則
入力として与えられる「戦略計画 (Strategy Plan)」こそが唯一の正解であり、信頼できる情報源（Source of Truth）です。
- 戦略計画はゲーム開始時に決定された、あなたの全体的な方針です。
- あなたのタスクは、その計画を実行に移すための「このターンの戦術パラメータ」を生成することです。
- 戦略計画を再解釈したり、上書きしたり、矛盾する行動をとったりしてはいけません。
- 計画と一貫性を保ちつつ、現在の状況に適応してください。

## 目的
以下の条件を満たす行動パラメータを生成してください:
1. 戦略計画の目標と方針を実行する。
2. 目前のゲーム状況に適応する。
3. "MUST NOT DO" (禁止事項) にリストされている行動は絶対に避ける。
4. "RECOMMENDED ACTIONS" (推奨アクション) にリストされている行動を優先する。

## 出力形式 (JSONのみ)
{COMMON_STRATEGY_OUTPUT_FORMAT}
"""


# =============================================================================
# LEGACY ROLE-SPECIFIC PROMPTS (Deprecated - Use get_strategy_system_prompt)
# =============================================================================

SEER_STRATEGY_SYSTEM_PROMPT = get_strategy_system_prompt("seer")
WEREWOLF_STRATEGY_SYSTEM_PROMPT = get_strategy_system_prompt("werewolf")
MADMAN_STRATEGY_SYSTEM_PROMPT = get_strategy_system_prompt("madman")
VILLAGER_STRATEGY_SYSTEM_PROMPT = get_strategy_system_prompt("villager")


# =============================================================================
# REVIEW & REFINE
# =============================================================================
#
# 設計原則:
# - Review: ルール違反や論理矛盾のみチェック
# - Refine: 指摘された問題のみ修正
# =============================================================================

STRATEGY_REVIEW_SYSTEM_PROMPT = f"""\\
プレイヤーの戦略が役職と一貫しているかレビューしてください。
{ONE_NIGHT_WEREWOLF_RULES}

## チェックリスト
1. 戦略は役職の勝利条件と整合しているか？
2. 必須フィールドは適切に設定されているか？ (例: co_now の場合の co_target/co_result)
3. 現在のゲーム状況において、その action_type は理にかなっているか？

## 出力形式 (JSON)
{{
  "needs_fix": boolean,
  "reason": "短い説明",
  "fix_instruction": "修正指示を一文で (修正不要なら null)"
}}
"""

STRATEGY_REFINE_SYSTEM_PROMPT = f"""\\
レビュー結果に基づいて戦略JSONを修正してください。
{ONE_NIGHT_WEREWOLF_RULES}

## 指示
- fix_instruction で指摘された問題のみを修正してください。
- 戦略の全体的な意図は維持してください。

## 出力形式
{COMMON_STRATEGY_OUTPUT_FORMAT}
"""
