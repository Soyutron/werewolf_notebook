from typing import Protocol, TYPE_CHECKING
from src.core.types.player import PlayerState
from copy import deepcopy

if TYPE_CHECKING:
    from src.graphs.player.player_graph import PlayerGraph


class PlayerController(Protocol):
    """
    プレイヤーに行動させるための Controller インターフェース。

    人間プレイヤー / AI プレイヤー / テスト用ダミーなどの違いを吸収し、
    GameSession からは「state を渡すと、新しい state が返ってくる」
    という共通の呼び出し方法で扱えるようにする。

    Controller 自体は state を「所有」せず、
    あくまで次の state を計算する責務のみを持つ。
    """

    def act(
        self,
        *,
        state: PlayerState,
    ) -> PlayerState:
        """
        現在の PlayerState を受け取り、
        プレイヤーの思考・判断・行動を反映した
        新しい PlayerState を返す。

        - state は Session が保持している元の状態
        - 戻り値は Controller によって計算された次の状態
        """
        ...


class AIPlayerController:
    """
    AI プレイヤー用の Controller 実装。

    PlayerGraph（LangGraph などで構築された思考エンジン）を用いて、
    プレイヤーの判断・行動を state 遷移として計算する。

    このクラスは PlayerGraph の薄いアダプタとして振る舞い、
    GameSession と PlayerGraph を直接結合させないための
    境界（Boundary）の役割を担う。
    """

    def __init__(self, player_graph: "PlayerGraph"):
        self.player_graph = player_graph

    def act(
        self,
        *,
        state: PlayerState,
    ) -> PlayerState:
        """
        Session から渡された PlayerState を元に、
        PlayerGraph を実行して次の PlayerState を生成する。

        注意点:
        - Session が保持している state を直接変更しないため、
          deepcopy により作業用の state（working_state）を作成する
        - state の最終的な確定保存は Session の責務
        """

        # Session が所有する state を破壊しないための作業用コピー
        working_state = deepcopy(state)

        # PlayerGraph による思考・行動の実行（state 遷移）
        new_state = self.player_graph.invoke(working_state)

        # 計算された新しい state を Session に返す
        return new_state
