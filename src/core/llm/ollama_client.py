from langchain_ollama import ChatOllama
from pydantic import BaseModel
from typing import TypeVar, Generic, Type

T = TypeVar("T", bound=BaseModel)


class OllamaLangChainClient(Generic[T]):
    """
    LangChain + Ollama を用いた LLMClient の具体実装。

    責務:
    - Ollama 上のローカル LLM を呼び出す
    - system / prompt を受け取り、LLM に渡す
    - 出力を指定された型（構造化データ）として返す

    設計上のポイント:
    - LangChain 依存はこのクラスに閉じ込める
    - 上位レイヤー（UseCase / Node 等）は LangChain を直接知らない
    - LLM の差し替え（Dummy / vLLM / OpenAI 等）を容易にする
    """

    def __init__(self, model: str, output_model: Type[T]):
        """
        OllamaLangChainClient を初期化する。

        Args:
            model: Ollama で使用するモデル名
                   例: "gemma3:1b", "gemma3:4b", "qwen2.5" など
        """

        # Ollama をバックエンドとする ChatModel
        # temperature は「揺らぎ」を抑え、内省の再現性を高めるため低めに設定
        self.llm = ChatOllama(
            model=model,
            temperature=0.3,
        )

        # LLM の出力を指定された型（構造化データ）として強制的に構造化するラッパー
        #
        # - LLM は JSON 形式で出力することを期待される
        # - パースに失敗した場合、LangChain 側で例外が発生する
        # - 呼び出し側では「Reflection が返る」ことを前提にできる
        self.structured_llm = self.llm.with_structured_output(output_model)

    def generate(self, *, system: str, prompt: str) -> T:
        """
        LLM に system / prompt を渡し、指定された型（構造化データ）を生成する。

        Args:
            system: system プロンプト（役割・制約・フォーマット定義など）
            prompt: human プロンプト（観測したイベントや状況）

        Returns:
            T:
                LLM が生成した内省結果。
                with_structured_output により、必ず指定された型になる。

        注意:
        - このメソッドは「同期的」に LLM を呼び出す
        - 失敗時の例外ハンドリングは上位レイヤーに委ねる設計
        """

        # LangChain が期待する message 形式
        # ("system", "..."), ("human", "...") のタプルで渡す
        messages = [
            ("system", system),
            ("human", prompt),
        ]

        # 構造化 LLM を実行
        # - LLM 呼び出し
        # - JSON 出力
        # - 指定された型へのパース
        # をまとめて行う
        result = self.structured_llm.invoke(messages)

        return result
