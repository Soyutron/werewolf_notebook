from src.core.types import PlayerState, PlayerOutput
from typing import Protocol


class PlayerGraph(Protocol):
    """
    Player の思考エンジンの共通インターフェース。

    - プレイヤーが「与えられた入力（PlayerInput）」に対して
      どのような行動（PlayerOutput）を返すかを決定する責務を持つ
    - LangGraph 実装 / ダミー実装 / テスト用スタブなどを
      差し替え可能にするため Protocol として定義している
    - state は GameSession が所有し、PlayerGraph は
      「受け取って → 更新して → 返す」だけの純粋な計算単位
    """

    def invoke(self, state: PlayerState) -> PlayerState:
        """
        与えられた PlayerState を入力として受け取り、
        次の PlayerState を返す。

        - state の中身（memory / input / output）をどこまで
          変更するかは PlayerGraph の実装に委ねられる
        - 副作用（DB 書き込みなど）は持たない想定
        """
        ...


class DummyPlayerGraph:
    """
    仮実装の PlayerGraph。

    - input.request が存在する場合:
        request の内容をそのまま PlayerOutput に変換する
    - input.request が存在しない場合:
        「待機ターン」とみなし output は None のまま返す

    設計検証・Session / Controller の動作確認用。
    思考ロジックや戦略判断は一切含まない。
    """

    def invoke(self, state: PlayerState) -> PlayerState:
        # GM から渡された「このターンの入力」を取得
        request = state["input"].request

        # 行動要求がない = 待機ターン
        # memory 等は変更せず、output も生成しない
        if request is None:
            state["output"] = None
            return state

        # 行動要求がある場合は、
        # request の内容をそのまま output に変換するだけ
        # （判断・分岐・推論などは一切行わない）
        state["output"] = PlayerOutput(
            action=request.request_type,
            payload=request.payload,
        )

        # 更新済みの state を返却
        return state


# 仮の PlayerGraph インスタンス
# - Session や Controller に注入して動作確認に使う
# - 後から LangGraph 実装に差し替える前提
player_graph = DummyPlayerGraph()
