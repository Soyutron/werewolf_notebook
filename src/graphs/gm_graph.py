from src.core.types import GameDecision, GMGraphState


class DummyGMGraph:
    """
    仮の GMGraph
    ・gm_state を読む
    ・1 ステップ分の GameDecision を decision に詰めて返す
    """

    def invoke(self, state: GMGraphState) -> GMGraphState:
        gm_state = state["gm_state"]
        phase = gm_state["phase"]

        decision: GameDecision = {}

        if phase == "night":
            decision["requests"] = {
                player: {
                    "request_type": "use_ability",
                    "payload": {
                        "candidates": [
                            p for p in gm_state["players"]
                            if p != player
                        ]
                    },
                }
                for player in gm_state["players"]
            }

            # 夜はまだ続く（結果待ち）
            decision["next_phase"] = None

        else:
            decision["next_phase"] = "reveal"

        return {
            "gm_state": gm_state,   # immutable
            "decision": decision,  # working memory
        }



# 仮の GMGraph
gm_graph = DummyGMGraph()
