from typing import TypedDict


class Reaction(TypedDict):
    """
    プレイヤーの反応ログ（LLM由来）。

    重要:
    - ゲームロジックには影響しない
    - 誤っていてもよい
    - いつでも破棄・無効化できる
    """

    kind: str
    text: str
