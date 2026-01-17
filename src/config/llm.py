# src/config/llm.py
"""
LLM クライアント生成に関する設定モジュール。

このファイルの責務:
- 用途ごと（内省 / 反応 など）に適切な LLM を選択する
- 実装側（PlayerGraph / Node / Generator）が
  「どのモデルを使うか」を意識しなくて済むようにする
- テストやデバッグ時に DummyLLM へ一括切り替えできるようにする
"""

from src.core.llm.ollama_client import OllamaLangChainClient
from src.core.llm.vllm_client import VLLMLangChainClient
from src.core.llm.dummy import DummyLLMClient
from src.core.llm.client import LLMClient
from src.core.memory.reflection import Reflection
from src.core.memory.reaction import Reaction
from src.core.memory.gm_comment import GMComment
from src.core.memory.speak import Speak
from src.core.memory.belief import RoleBeliefsOutput
from src.core.memory.gm_maturity import GMMaturityDecision

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
USE_VLLM = True


# =========================================================
# 内省（Reflection）用 LLM
# =========================================================
def create_reflection_llm() -> LLMClient[Reflection]:
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

    if USE_VLLM:
        # 実運用用
        # gemma3:12b は推論能力が高く、内省用途に向いている
        return VLLMLangChainClient(
            model="google/gemma-3-12b-it", output_model=Reflection
        )

    # 実運用用
    # gemma3:12b は推論能力が高く、内省用途に向いている
    return OllamaLangChainClient(model="gemma3:1b", output_model=Reflection)


# =========================================================
# 反応（Reaction / 即時応答）用 LLM
# =========================================================
def create_reaction_llm() -> LLMClient[Reaction]:
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

    if USE_VLLM:
        # 実運用用
        # gemma3:12b は推論能力が高く、内省用途に向いている
        return VLLMLangChainClient(model="google/gemma-3-12b-it", output_model=Reaction)

    # 実運用用
    # gemma3:1b は軽量で応答が速く、リアクション用途に最適
    return OllamaLangChainClient(model="gemma3:1b", output_model=Reaction)


def create_gm_comment_llm() -> LLMClient[GMComment]:
    """
    GM が観測した public_event から
    次の speaker と進行コメントを生成する。
    """

    if USE_DUMMY:
        # テスト・デバッグ用
        return DummyLLMClient()

    if USE_VLLM:
        # 実運用用
        # gemma3:12b は推論能力が高く、内省用途に向いている
        return VLLMLangChainClient(
            model="google/gemma-3-12b-it", output_model=GMComment
        )

    # 実運用用
    # gemma3:12b は推論能力が高く、内省用途に向いている
    return OllamaLangChainClient(model="gemma3:12b", output_model=GMComment)

def create_gm_maturity_llm() -> LLMClient[GMMaturityDecision]:
    """
    GM が議論の成熟度を判定する。
    """

    if USE_DUMMY:
        # テスト・デバッグ用
        return DummyLLMClient()

    if USE_VLLM:
        # 実運用用
        # gemma3:12b は推論能力が高く、内省用途に向いている
        return VLLMLangChainClient(
            model="google/gemma-3-12b-it", output_model=GMMaturityDecision
        )

    # 実運用用
    # gemma3:12b は推論能力が高く、内省用途に向いている
    return OllamaLangChainClient(model="gemma3:12b", output_model=GMMaturityDecision)


def create_speak_llm() -> LLMClient[Speak]:
    """
    GM が観測した public_event から
    次の speaker と進行コメントを生成する。
    """

    if USE_DUMMY:
        # テスト・デバッグ用
        return DummyLLMClient()

    if USE_VLLM:
        # 実運用用
        # gemma3:12b は推論能力が高く、内省用途に向いている
        return VLLMLangChainClient(model="google/gemma-3-12b-it", output_model=Speak)

    # 実運用用
    # gemma3:12b は推論能力が高く、内省用途に向いている
    return OllamaLangChainClient(model="gemma3:12b", output_model=Speak)

def create_belief_llm() -> LLMClient[RoleBeliefsOutput]:
    if USE_DUMMY:
        return DummyLLMClient(output=RoleBeliefsOutput)

    if USE_VLLM:
        return VLLMLangChainClient(
            model="google/gemma-3-12b-it",
            output_model=RoleBeliefsOutput,
        )

    return OllamaLangChainClient(
        model="gemma3:12b",
        output_model=RoleBeliefsOutput,
    )