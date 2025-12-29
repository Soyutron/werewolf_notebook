from langchain_ollama import ChatOllama


class LangChainClient:
    """
    LangChain を使った LLMClient 実装。
    """

    def __init__(self, model: str):
        self.llm = ChatOllama(
            model=model,
            temperature=0.3,
        )

    def generate(self, *, system: str, prompt: str) -> str:
        messages = [
            ("system", system),
            ("human", prompt),
        ]

        result = self.llm.invoke(messages)
        return result.content
