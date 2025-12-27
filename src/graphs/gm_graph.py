from src.core.types import GameDecision


class DummyGMGraph:
    """
    仮の GMGraph
    ・gm_state を見て
    ・次にやるべき 1 アクションだけ返す
    """

    def invoke(self, gm_state) -> GameDecision:
        phase = gm_state["phase"]

        if phase == "night":
            # とりあえず占い師に行動させるだけ
            return {
                "type": "request_player",
                "payload": {
                    "player": "太郎",  # 仮
                    "input": {
                        "request": {
                            "request_type": "use_ability",
                            "payload": {
                                "candidates": ["花子", "次郎"],
                            },
                        }
                    },
                },
            }

        return {
            "type": "end_game",
            "payload": {},
        }


# 仮の GMGraph
gm_graph = DummyGMGraph()
