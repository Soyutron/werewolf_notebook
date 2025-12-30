from typing import Protocol, TypeVar
from pydantic import BaseModel

T = TypeVar("T", bound=BaseModel)


class LLMClient(Protocol[T]):
    """
    LLM 呼び出しのための抽象インターフェース（Protocol）。

    目的:
    - 実際の LLM 実装（Ollama / vLLM / Dummy など）を
      呼び出し側から完全に切り離すための契約（contract）を定義する
    - ゲームロジック・Graph・UseCase 層が
      「どの LLM を使っているか」を意識しなくて済む設計にする

    設計方針:
    - 継承ではなく Protocol（構造的部分型）を使うことで、
      実装クラスに依存しない柔軟な差し替えを可能にする
    - ランタイムではなく「型チェック時」に契約を保証する
    - LangChain / Ollama / 自作クライアントを混在させても破綻しない

    このインターフェースが保証すること:
    - 同期的に 1 回の生成を行う
    - system / prompt を明示的に分離して受け取る
    - 生成結果は純粋な str として返す
      （ストリーミング・トークン列・メタ情報は扱わない）

    想定する実装例:
    - OllamaLangChainClient（Ollama のラッパ）
    - DummyLLMClient（テスト・デバッグ用の固定応答）
    """

    def generate(self, *, system: str, prompt: str) -> T:
        """
        LLM に system / prompt を渡し、生成結果を指定された型（構造化データ）として返す。

        引数:
        - system:
            LLM に与える system プロンプト。
            役割・人格・制約・思考スタイルなどを定義する。
        - prompt:
            その時点の入力文。
            観測イベント・リクエスト・文脈要約などを含む。

        戻り値:
        - LLM が生成したテキスト（加工前の生文字列）
          指定された型（構造化データ）にパースして返す

        注意:
        - 例外処理・リトライ・タイムアウト制御は
          実装クラス側の責務とする
        - 呼び出し側は「必ず文字列が返る」前提で扱ってよい

        使用例:
            result = client.generate(
                system="You are a cautious werewolf player.",
                prompt="Player A accused Player B."
            )
        """
        ...
