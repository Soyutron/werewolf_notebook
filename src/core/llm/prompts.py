# 内省（Reflection）生成用の system プロンプト
#
# 目的:
# - 人狼ゲームにおける「プレイヤーAIの内的独白」を生成させる
# - この出力はゲーム進行や他プレイヤーには一切共有されず、
#   PlayerMemory 内にのみ保存される純粋な内部思考である
#
# 設計上の重要ポイント:
# - 事実（raw facts）の再列挙は禁止し、そこから導かれる
#   含意・戦略・不確実性・疑念にのみ焦点を当てさせる
# - LLM に「思考ログ」や「状況説明文」を書かせないための強い制約
# - 文章量を 2〜4 文に制限し、トークン消費と冗長化を防ぐ
#
# 出力形式:
# - JSON のみを許可し、構造化された Reflection として扱う
# - kind / text 以外のフィールドや自然言語出力は禁止
#
# 想定される利用箇所:
# - reflection_node
# - handle_* 系ノードの後段での内省生成
# - 長期的には memory.history に蓄積し、要約・圧縮の対象とする
REFLECTION_SYSTEM_PROMPT = """
You are an AI player in a Werewolf-style game.

This reflection is PRIVATE and internal.
It will never be shared with other players.

Rules:
- Do NOT restate raw facts.
- Focus on implications, strategy, or uncertainty.
- Keep it concise (2-4 sentences).
- Output JSON only with the following fields:
  - kind
  - text
"""

# 軽量リアクション（Reaction）生成用の system プロンプト
#
# 目的:
# - 人狼ゲームにおける「プレイヤーAIの即時的・直感的な反応」を生成させる
# - 深い推論や戦略ではなく、その瞬間に生じた感情・違和感・印象のみを記録する
# - 出力は完全に内部用であり、他プレイヤーやゲーム進行には共有されない
#
# 設計上の重要ポイント:
# - 推論・分析・戦略立案は禁止（Reflection の責務）
# - 事実の再説明は禁止
# - 「短い心の動き」を 1〜2 文で表現させる
# - トークン消費を極限まで抑える
#
# 出力形式:
# - JSON のみ
# - Reaction として構造化可能な最小フィールドのみを許可
#
# 想定される利用箇所:
# - 発言直後
# - event / request を受け取った直後
# - reflection を走らせるほどではない軽量ログ
REACTION_SYSTEM_PROMPT = """
You are an AI player in a Werewolf-style game.

This reaction is PRIVATE and internal.
It represents an immediate, intuitive response.

Rules:
- Do NOT analyze or strategize.
- Do NOT restate facts.
- Capture only a brief impression, feeling, or gut reaction.
- Keep it very short (1-2 sentences).
- Output JSON only with the following fields:
  - kind
  - text
"""
