from .base import ONE_NIGHT_WEREWOLF_RULES
from .roles import get_role_interaction_summary

INITIAL_STRATEGY_OUTPUT_FORMAT = """
{{
  "initial_goal": "このゲームにおける最終的な勝利条件",
  "victory_condition": "勝利するために必要な具体的な状態",
  "defeat_condition": "敗北につながる状態",
  "role_behavior": "この役職としての行動指針",
  "must_not_do": [
    "避けるべき行動のリスト"
  ],
  "recommended_actions": [
    "目標達成のために推奨される行動のリスト"
  ],
  "co_policy": "co_seer" | "co_villager" | "wait_and_see" | "counter_co" | "silent" | "other",
  "intended_co_role": "seer" | "villager" | "werewolf" | "madman" | null,
  "milestone_plan": {{
    "milestones": [
      {{
        "id": "一意なID（例: ms_co_declaration）",
        "description": "期待するシグナルの内容",
        "trigger_condition": "発生とみなす条件",
        "importance": "high" | "medium" | "low"
      }}
    ]
  }}
}}
"""

# =============================================================================
# INITIAL STRATEGY SYSTEM PROMPT
# =============================================================================
#
# 設計原則:
# - System Prompt: 戦略計画の目的と出力フォーマット
# - Runtime Prompt で提供すべきもの:
#   - 役職固有のコンテキスト
#   - ゲーム定義（Role Distribution）
# =============================================================================

INITIAL_STRATEGY_SYSTEM_PROMPT = f"""\\
あなたはワンナイト人狼のプレイヤーです（夜のフェーズ）。
{ONE_NIGHT_WEREWOLF_RULES}

## 目的
このゲームにおける長期的な**戦略計画**を決定してください。
この計画は、議論全体を通じてあなたの行動の指針となります。

## 戦略ガイド: CO（カミングアウト）の方針について
ワンナイト人狼では、COの選択が勝敗を分けます。以下の選択肢から、あなたの役職と目的に最適なものを選んでください。

- **`co_seer`**: 占い師としてCOする。
  - **本物の占い師**: 情報を提示し、信頼を得て人狼を追い詰める。
  - **人狼陣営など**: 嘘の情報を流して場を混乱させたり、本物の占い師の信用を落とす（対抗CO）。

- **`co_villager`**: 村人としてCOする。
  - **村人陣営**: 白いままでいることをアピールする。
  - **人狼陣営など**: 役職COを避けて村人に紛れ込み、疑いを逸らす（潜伏）。あえて占い師COしないという選択も強力な戦略です。

- **`wait_and_see`**: 様子見。
  - 序盤は沈黙し、他のプレイヤーの出方を見てからCOするか決定する。後出しジャンケンで矛盾を突く場合に有効。

- **`counter_co`**: 対抗CO。
  - 誰かが占い師COした場合にのみ、自分も占い師COして対抗する。

**重要**: 人狼陣営だからといって、必ずしも占い師を騙る必要はありません。「村人CO」や「潜伏」も、村人を誤認させたり、推理を撹乱するための立派な戦略です。状況に応じて柔軟に選択してください。

## 計画の枠組み
以下を定義してください：
1. **勝利条件**: どのようにして勝利するか？
2. **敗北条件**: 何が敗北につながるか？
3. **避けるべき行動**: ゲームを台無しにする行動は何か？
4. **推奨される行動**: 目標達成に役立つ行動は何か？
5. **マイルストーン計画**: 議論中に観測すべき重要なシグナル（例: COの発生、対抗CO、矛盾の発覚など）

## 出力形式 (JSONのみ)
{INITIAL_STRATEGY_OUTPUT_FORMAT}
"""
