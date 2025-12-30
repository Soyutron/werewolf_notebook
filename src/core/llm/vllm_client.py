from typing import TypeVar, Generic, Type
from pydantic import BaseModel
import json

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
            model_kwargs={
                "extra_body": {
                    "guided_json": self.output_model.model_json_schema()
                }
            }
        )

    def generate(self, *, system: str, prompt: str) -> T:
        """
        system / prompt を渡し、構造化データを生成する。
        """

        # JSON出力を強制する system prompt を合成
        schema_json = self.output_model.model_json_schema()

        structured_system = f"""
{system}

You MUST output valid JSON.
The JSON MUST conform to the following schema:
{json.dumps(schema_json, ensure_ascii=False, indent=2)}

Do not include any extra text.
"""

        messages = [
            ("system", structured_system),
            ("human", prompt),
        ]

        result = self.llm.invoke(messages)

        # vLLM は text として返るので自前パース
        try:
            data = json.loads(result.content)
            return self.output_model.model_validate(data)
        except Exception as e:
            raise ValueError(
                f"Failed to parse structured output: {result.content}"
            ) from e
