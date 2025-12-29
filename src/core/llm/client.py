from typing import Protocol


class LLMClient(Protocol):
    """
    LLM 呼び出しの抽象インターフェース。

    このインターフェースは以下を保証する:
    - 同期的に 1 回の生成を行う
    - system / prompt を受け取り
    - 生成結果を str として返す

    実装例:
    - OllamaClient
    - VLLMClient
    - DummyClient（テスト用）
    """

    def generate(self, *, system: str, prompt: str) -> str:
        """
        LLM にプロンプトを渡し、生成結果を返す。

        例:
            result = client.generate(
                system="You are ...",
                prompt="New event is ..."
            )
        """
        ...
