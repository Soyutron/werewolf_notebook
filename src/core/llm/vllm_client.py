from typing import TypeVar, Generic, Type
from pydantic import BaseModel
from langchain_openai import ChatOpenAI

T = TypeVar("T", bound=BaseModel)


class VLLMLangChainClient(Generic[T]):
    """
    LangChain + vLLM(OpenAI互換API) を用いた LLMClient 実装。

    設計方針:
    - vLLM は常駐・高速推論を担当
    - 構造化は「JSON出力 + Pydanticパース」で制御
    - LangChain 依存はこのクラスに閉じ込める
    """

    def __init__(
        self,
        *,
        model: str,
        output_model: Type[T],
        base_url: str = "http://localhost:8000/v1",
        api_key: str = "EMPTY",
    ):
        """
        Args:
            model: vLLM でロードしているモデル名
            output_model: 期待する出力の Pydantic Model
            base_url: vLLM の OpenAI 互換エンドポイント
        """

        self.output_model = output_model

        self.llm = ChatOpenAI(
            model=model,
            base_url=base_url,
            api_key=api_key,
            temperature=0.3,
            # extra_body={
            #     "guided_json": self.output_model.model_json_schema(),
            # },
        )
        # LLM の出力を指定された型（構造化データ）として強制的に構造化するラッパー
        #
        # - LLM は JSON 形式で出力することを期待される
        # - パースに失敗した場合、LangChain 側で例外が発生する
        # - 呼び出し側では「Reflection が返る」ことを前提にできる
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

        # 構造化 LLM を実行
        # - LLM 呼び出し
        # - JSON 出力
        # - 指定された型へのパース
        # をまとめて行う
        result = self.structured_llm.invoke(messages)

        return result
