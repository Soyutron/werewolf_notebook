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
from src.core.llm.gemini_client import GeminiLangChainClient
from src.core.llm.dummy import DummyLLMClient
from src.core.llm.client import LLMClient
from src.core.memory.reflection import Reflection
from src.core.memory.reaction import Reaction
from src.core.memory.gm_comment import GMComment
from src.core.memory.speak import Speak
from src.core.memory.belief import RoleBeliefsOutput
from src.core.memory.gm_maturity import GMMaturityDecision
from src.core.memory.vote import VoteOutput
from src.core.memory.gm_comment_review import GMCommentReviewResult
from src.core.memory.strategy import Strategy, StrategyReview, SpeakReview, StrategyPlan
from src.core.memory.log_summary import LogSummaryOutput
from src.core.memory.gm_plan import GMProgressionPlan

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
USE_VLLM = False
USE_GEMINI = True

# Gemini API 設定
# 使用するモデル名（gemini-2.0-flash, gemini-1.5-pro など）
GEMINI_MODEL = "gemini-2.5-flash-lite"
GEMINI_MODEL_2 = "gemini-2.5-flash"


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
    - 高性能・大きめモデル（nemotron-3-nano:30b）を使用する
    """

    if USE_DUMMY:
        # テスト・デバッグ用
        # 内省ロジックの流れだけを確認したい場合に使用
        return DummyLLMClient()

    if USE_GEMINI:
        # Gemini API を使用
        return GeminiLangChainClient(model=GEMINI_MODEL, output_model=Reflection)

    if USE_VLLM:
        # 実運用用
        # nemotron-3-nano:30b は推論能力が高く、内省用途に向いている
        return VLLMLangChainClient(
            model="google/gemma-3-12b-it", output_model=Reflection
        )

    # 実運用用
    # nemotron-3-nano:30b は推論能力が高く、内省用途に向いている
    return OllamaLangChainClient(model="nemotron-3-nano:30b", output_model=Reflection)


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
    - 軽量・高速モデル（nemotron-3-nano:30b）を使用する
    """

    if USE_DUMMY:
        # テスト・デバッグ用
        return DummyLLMClient()

    if USE_GEMINI:
        # Gemini API を使用
        return GeminiLangChainClient(model=GEMINI_MODEL, output_model=Reaction)

    if USE_VLLM:
        # 実運用用
        # nemotron-3-nano:30b は推論能力が高く、内省用途に向いている
        return VLLMLangChainClient(model="google/gemma-3-12b-it", output_model=Reaction)

    # 実運用用
    # nemotron-3-nano:30b は軽量で応答が速く、リアクション用途に最適
    return OllamaLangChainClient(model="nemotron-3-nano:30b", output_model=Reaction)


def create_gm_comment_llm() -> LLMClient[GMComment]:
    """
    GM が観測した public_event から
    次の speaker と進行コメントを生成する。
    """

    if USE_DUMMY:
        # テスト・デバッグ用
        return DummyLLMClient()

    if USE_GEMINI:
        # Gemini API を使用
        return GeminiLangChainClient(model=GEMINI_MODEL, output_model=GMComment)

    if USE_VLLM:
        # 実運用用
        # nemotron-3-nano:30b は推論能力が高く、内省用途に向いている
        return VLLMLangChainClient(
            model="google/gemma-3-12b-it", output_model=GMComment
        )

    # 実運用用
    # nemotron-3-nano:30b は推論能力が高く、内省用途に向いている
    return OllamaLangChainClient(model="nemotron-3-nano:30b", output_model=GMComment)


def create_gm_maturity_llm() -> LLMClient[GMMaturityDecision]:
    """
    GM が議論の成熟度を判定する。
    """

    if USE_DUMMY:
        # テスト・デバッグ用
        return DummyLLMClient()

    if USE_GEMINI:
        # Gemini API を使用
        return GeminiLangChainClient(model=GEMINI_MODEL, output_model=GMMaturityDecision)

    if USE_VLLM:
        # 実運用用
        # nemotron-3-nano:30b は推論能力が高く、内省用途に向いている
        return VLLMLangChainClient(
            model="google/gemma-3-12b-it", output_model=GMMaturityDecision
        )

    # 実運用用
    # nemotron-3-nano:30b は推論能力が高く、内省用途に向いている
    return OllamaLangChainClient(
        model="nemotron-3-nano:30b", output_model=GMMaturityDecision
    )


def create_speak_llm() -> LLMClient[Speak]:
    """
    GM が観測した public_event から
    次の speaker と進行コメントを生成する。
    """

    if USE_DUMMY:
        # テスト・デバッグ用
        return DummyLLMClient()

    if USE_GEMINI:
        # Gemini API を使用
        return GeminiLangChainClient(model=GEMINI_MODEL_2, output_model=Speak)

    if USE_VLLM:
        # 実運用用
        # nemotron-3-nano:30b は推論能力が高く、内省用途に向いている
        return VLLMLangChainClient(model="google/gemma-3-12b-it", output_model=Speak)

    # 実運用用
    # nemotron-3-nano:30b は推論能力が高く、内省用途に向いている
    return OllamaLangChainClient(model="nemotron-3-nano:30b", output_model=Speak)


def create_belief_llm() -> LLMClient[RoleBeliefsOutput]:
    if USE_DUMMY:
        return DummyLLMClient(output=RoleBeliefsOutput)

    if USE_GEMINI:
        return GeminiLangChainClient(model=GEMINI_MODEL, output_model=RoleBeliefsOutput)

    if USE_VLLM:
        return VLLMLangChainClient(
            model="google/gemma-3-12b-it",
            output_model=RoleBeliefsOutput,
        )

    return OllamaLangChainClient(
        model="nemotron-3-nano:30b",
        output_model=RoleBeliefsOutput,
    )


def create_vote_llm() -> LLMClient[VoteOutput]:
    if USE_DUMMY:
        return DummyLLMClient(output=VoteOutput)

    if USE_GEMINI:
        return GeminiLangChainClient(model=GEMINI_MODEL, output_model=VoteOutput)

    if USE_VLLM:
        return VLLMLangChainClient(
            model="google/gemma-3-12b-it",
            output_model=VoteOutput,
        )

    return OllamaLangChainClient(
        model="nemotron-3-nano:30b",
        output_model=VoteOutput,
    )


def create_gm_comment_reviewer_llm() -> LLMClient[GMCommentReviewResult]:
    if USE_DUMMY:
        return DummyLLMClient(output=GMCommentReviewResult)

    if USE_GEMINI:
        return GeminiLangChainClient(model=GEMINI_MODEL, output_model=GMCommentReviewResult)

    if USE_VLLM:
        return VLLMLangChainClient(
            model="google/gemma-3-12b-it",
            output_model=GMCommentReviewResult,
        )

    return OllamaLangChainClient(
        model="nemotron-3-nano:30b",
        output_model=GMCommentReviewResult,
    )


def create_gm_comment_refiner_llm() -> LLMClient[GMComment]:
    """
    GM が観測した public_event から
    次の speaker と進行コメントを生成する。
    """

    if USE_DUMMY:
        # テスト・デバッグ用
        return DummyLLMClient()

    if USE_GEMINI:
        # Gemini API を使用
        return GeminiLangChainClient(model=GEMINI_MODEL, output_model=GMComment)

    if USE_VLLM:
        # 実運用用
        # nemotron-3-nano:30b は推論能力が高く、内省用途に向いている
        return VLLMLangChainClient(
            model="google/gemma-3-12b-it", output_model=GMComment
        )

    # 実運用用
    # nemotron-3-nano:30b は推論能力が高く、内省用途に向いている
    return OllamaLangChainClient(model="nemotron-3-nano:30b", output_model=GMComment)


# =========================================================
# 戦略（Strategy）生成用 LLM
# =========================================================
def create_strategy_llm() -> LLMClient[Strategy]:
    """
    プレイヤーの発言前戦略を生成するための LLM を返す。
    """
    if USE_DUMMY:
        return DummyLLMClient()

    if USE_GEMINI:
        return GeminiLangChainClient(model=GEMINI_MODEL, output_model=Strategy)

    if USE_VLLM:
        return VLLMLangChainClient(
            model="google/gemma-3-12b-it", output_model=Strategy
        )

    return OllamaLangChainClient(model="nemotron-3-nano:30b", output_model=Strategy)


def create_strategy_plan_llm() -> LLMClient[StrategyPlan]:
    """
    プレイヤーの初期戦略計画（StrategyPlan）を生成するための LLM を返す。
    """
    if USE_DUMMY:
        return DummyLLMClient()

    if USE_GEMINI:
        return GeminiLangChainClient(model=GEMINI_MODEL, output_model=StrategyPlan)

    if USE_VLLM:
        return VLLMLangChainClient(
            model="google/gemma-3-12b-it", output_model=StrategyPlan
        )

    return OllamaLangChainClient(model="nemotron-3-nano:30b", output_model=StrategyPlan)


def create_strategy_reviewer_llm() -> LLMClient[StrategyReview]:
    """
    戦略をレビューするための LLM を返す。
    """
    if USE_DUMMY:
        return DummyLLMClient()

    if USE_GEMINI:
        return GeminiLangChainClient(model=GEMINI_MODEL, output_model=StrategyReview)

    if USE_VLLM:
        return VLLMLangChainClient(
            model="google/gemma-3-12b-it", output_model=StrategyReview
        )

    return OllamaLangChainClient(
        model="nemotron-3-nano:30b", output_model=StrategyReview
    )


def create_strategy_refiner_llm() -> LLMClient[Strategy]:
    """
    戦略を修正するための LLM を返す。
    """
    if USE_DUMMY:
        return DummyLLMClient()

    if USE_GEMINI:
        return GeminiLangChainClient(model=GEMINI_MODEL, output_model=Strategy)

    if USE_VLLM:
        return VLLMLangChainClient(
            model="google/gemma-3-12b-it", output_model=Strategy
        )

    return OllamaLangChainClient(model="nemotron-3-nano:30b", output_model=Strategy)


def create_speak_reviewer_llm() -> LLMClient[SpeakReview]:
    """
    発言をレビューするための LLM を返す。
    """
    if USE_DUMMY:
        return DummyLLMClient()

    if USE_GEMINI:
        return GeminiLangChainClient(model=GEMINI_MODEL, output_model=SpeakReview)

    if USE_VLLM:
        return VLLMLangChainClient(
            model="google/gemma-3-12b-it", output_model=SpeakReview
        )

    return OllamaLangChainClient(
        model="nemotron-3-nano:30b", output_model=SpeakReview
    )


def create_speak_refiner_llm() -> LLMClient[Speak]:
    """
    発言を修正するための LLM を返す。
    """
    if USE_DUMMY:
        return DummyLLMClient()

    if USE_GEMINI:
        return GeminiLangChainClient(model=GEMINI_MODEL, output_model=Speak)

    if USE_VLLM:
        return VLLMLangChainClient(
            model="google/gemma-3-12b-it", output_model=Speak
        )

    return OllamaLangChainClient(model="nemotron-3-nano:30b", output_model=Speak)


# =========================================================
# ログ要約（Log Summary）用 LLM
# =========================================================
def create_log_summarizer_llm() -> LLMClient[LogSummaryOutput]:
    """
    ゲームログの差分要約を行うための LLM を返す。
    
    特徴:
    - 要約能力が重要
    - 情報の選別・圧縮が求められる
    """
    if USE_DUMMY:
        return DummyLLMClient()

    if USE_GEMINI:
        return GeminiLangChainClient(model=GEMINI_MODEL, output_model=LogSummaryOutput)

    if USE_VLLM:
        return VLLMLangChainClient(
            model="google/gemma-3-12b-it", output_model=LogSummaryOutput
        )

    return OllamaLangChainClient(
        model="nemotron-3-nano:30b", output_model=LogSummaryOutput
    )


# =========================================================
# GM 進行計画（Progression Plan）用 LLM
# =========================================================
def create_gm_plan_llm() -> LLMClient[GMProgressionPlan]:
    """
    GM の進行計画（Progression Plan）を生成するための LLM を返す。
    """
    if USE_DUMMY:
        return DummyLLMClient(output=GMProgressionPlan(content="Dummy Plan"))

    if USE_GEMINI:
        return GeminiLangChainClient(model=GEMINI_MODEL, output_model=GMProgressionPlan)

    if USE_VLLM:
        return VLLMLangChainClient(
            model="google/gemma-3-12b-it", output_model=GMProgressionPlan
        )

    return OllamaLangChainClient(
        model="nemotron-3-nano:30b", output_model=GMProgressionPlan
    )
