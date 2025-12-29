from langchain_ollama import ChatOllama
from src.core.memory.reflection import Reflection


class LangChainClient:
    """
    LangChain を使った LLMClient 実装。
    """

    def __init__(self, model: str):
        self.llm = ChatOllama(
            model=model,
            temperature=0.3,
        )

        self.structured_llm = self.llm.with_structured_output(Reflection)

    def generate(self, *, system: str, prompt: str) -> Reflection:
        messages = [
            ("system", system),
            ("human", prompt),
        ]

        result = self.structured_llm.invoke(messages)
        return result
