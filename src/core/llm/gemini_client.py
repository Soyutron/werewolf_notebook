# src/core/llm/gemini_client.py
"""
Gemini API を LangChain 経由で利用する LLMClient 実装。

設計方針:
- LangChain の ChatGoogleGenerativeAI を使用
- 構造化は「.with_structured_output()」で制御
- LangChain 依存はこのクラスに閉じ込める
- 既存の VLLMLangChainClient / OllamaLangChainClient と同じインターフェース
"""

import os
from typing import TypeVar, Generic, Type
from pydantic import BaseModel
from langchain_google_genai import ChatGoogleGenerativeAI

T = TypeVar("T", bound=BaseModel)


class GeminiLangChainClient(Generic[T]):
    """
    LangChain + Gemini API を用いた LLMClient 実装。

    設計方針:
    - Gemini は Google Cloud / AI Studio の API を使用
    - 構造化は「JSON出力 + Pydanticパース」で制御
    - LangChain 依存はこのクラスに閉じ込める
    """

    def __init__(
        self,
        *,
        model: str = "gemini-2.0-flash",
        output_model: Type[T],
        api_key: str | None = None,
        temperature: float = 0.3,
    ):
        """
        Args:
            model: Gemini モデル名（例: gemini-2.0-flash, gemini-1.5-pro）
            output_model: 期待する出力の Pydantic Model
            api_key: Gemini API キー（省略時は環境変数 GOOGLE_API_KEY を使用）
            temperature: 生成温度（デフォルト 0.3）
        """

        self.output_model = output_model

        # API キーの取得
        # 1. 引数で渡された場合はそれを使用
        # 2. 環境変数 GOOGLE_API_KEY を使用
        resolved_api_key = api_key or os.environ.get("GOOGLE_API_KEY")

        if not resolved_api_key:
            raise ValueError(
                "Gemini API key is required. "
                "Set GOOGLE_API_KEY environment variable or pass api_key argument."
            )

        self.llm = ChatGoogleGenerativeAI(
            model=model,
            google_api_key=resolved_api_key,
            temperature=temperature,
            timeout=60,  # タイムアウト60秒
        )

        # LLM の出力を指定された型（構造化データ）として強制的に構造化するラッパー
        #
        # - LLM は JSON 形式で出力することを期待される
        # - パースに失敗した場合、LangChain 側で例外が発生する
        # - 呼び出し側では指定した型が返ることを前提にできる
        self.structured_llm = self.llm.with_structured_output(output_model)

    def generate(self, *, system: str, prompt: str) -> T:
        """
        system / prompt を渡し、構造化データを生成する。
        """

        # LangChain が期待する message 形式
        # ("system", "..."), ("human", "...") のタプルで渡す
        messages = [
            ("system", system),
            ("human", prompt),
        ]

        print(f"[GeminiClient] Invoking structured_llm for {self.output_model.__name__}...")
        
        try:
            # 構造化 LLM を実行
            # - LLM 呼び出し
            # - JSON 出力
            # - 指定された型へのパース
            # をまとめて行う
            result = self.structured_llm.invoke(messages)
            
            print(f"[GeminiClient] structured_llm.invoke returned for {self.output_model.__name__}")

            return result
        except Exception as e:
            print(f"[GeminiClient] Error invoking structured_llm for {self.output_model.__name__}: {e}")
            raise

    async def agenerate(self, *, system: str, prompt: str) -> T:
        """
        非同期版の generate メソッド。
        system / prompt を渡し、構造化データを生成する。
        """

        messages = [
            ("system", system),
            ("human", prompt),
        ]

        result = await self.structured_llm.ainvoke(messages)

        return result
