class DummyLLMClient:
    """
    テスト・デバッグ用のダミー LLM。

    - 常に固定の JSON を返す
    - LLM が無くても動作確認できる
    """

    def generate(self, *, system: str, prompt: str) -> str:
        return """
        {
            "kind": "reflection",
            "text": "新しい情報を得たが、まだ判断には慎重になる必要がある。"
        }
        """
