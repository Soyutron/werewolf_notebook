# src/config/llm.py
"""
LLM クライアント生成に関する設定モジュール。

このファイルの責務:
- 用途ごと（内省 / 反応 など）に適切な LLM を選択する
- 実装側（PlayerGraph / Node / Generator）が
  「どのモデルを使うか」を意識しなくて済むようにする
- テストやデバッグ時に DummyLLM へ一括切り替えできるようにする
"""

from src.core.llm.langchain import LangChainClient
from src.core.llm.dummy import DummyLLMClient
from src.core.llm.client import LLMClient

# =========================================================
# LLM 切り替えフラグ
# =========================================================
# True の場合:
#   - すべての LLM 呼び出しを DummyLLMClient に差し替える
#   - 推論時間ゼロ・外部依存なしでテスト可能
#
# False の場合:
#   - 実際のローカル / 外部 LLM を使用する
USE_DUMMY = False


# =========================================================
# 内省（Reflection）用 LLM
# =========================================================
def create_reflection_llm() -> LLMClient:
    """
    プレイヤーの「内省（reflection）」を生成するための LLM を返す。

    内省の特徴:
    - 推論・抽象化・一貫性が重要
    - 多少遅くてもよい
    - トークン消費はある程度許容される

    そのため:
    - 高性能・大きめモデル（gemma3:12b）を使用する
    """

    if USE_DUMMY:
        # テスト・デバッグ用
        # 内省ロジックの流れだけを確認したい場合に使用
        return DummyLLMClient()

    # 実運用用
    # gemma3:12b は推論能力が高く、内省用途に向いている
    return LangChainClient(model="gemma3:12b")


# =========================================================
# 反応（Reaction / 即時応答）用 LLM
# =========================================================
def create_reaction_llm() -> LLMClient:
    """
    プレイヤーの「即時反応・発言・軽い判断」を生成するための LLM を返す。

    反応の特徴:
    - 速度が最優先
    - 深い推論は不要
    - 呼び出し頻度が高くなりがち

    そのため:
    - 軽量・高速モデル（gemma3:1b）を使用する
    """

    if USE_DUMMY:
        # テスト・デバッグ用
        return DummyLLMClient()

    # 実運用用
    # gemma3:1b は軽量で応答が速く、リアクション用途に最適
    return LangChainClient(model="gemma3:1b")
