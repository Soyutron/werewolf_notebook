from typing import TypedDict, Literal


class Reflection(TypedDict):
    """
    プレイヤーの内省ログ（LLM由来）。

    重要:
    - ゲームロジックには影響しない
    - 誤っていてもよい
    - いつでも破棄・無効化できる
    """

    kind: Literal["reflection", "inference", "meta"]
    text: str
