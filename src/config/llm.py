# src/config/llm.py
from src.core.llm.langchain import LangChainClient
from src.core.llm.dummy import DummyLLMClient
from src.core.llm.client import LLMClient

USE_DUMMY = False


def create_reflection_llm() -> LLMClient:
    if USE_DUMMY:
        return DummyLLMClient()
    return LangChainClient(model="gemma3:12b")
