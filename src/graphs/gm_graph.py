from src.core.types import GameDecision, GMGraphState, PlayerRequest, GameEvent


class DummyGMGraph:
    """
    仮の GMGraph
    ・world_state を読む
    ・1 ステップ分の GameDecision を decision に詰めて返す
    """

    def invoke(self, state: GMGraphState) -> GMGraphState:
        world_state = state["world_state"]
        phase = world_state.phase

        decision = GameDecision()

        if phase == "night":
            decision.events.append(
                GameEvent(
                    event_type="phase_start",
                    payload={"phase": "night"}
                )
            )
            decision.requests = {
                player: PlayerRequest(
                    request_type="use_ability",
                    payload={
                        "candidates": [p for p in world_state.players if p != player]
                    },
                )
                for player in world_state.players
            }

            # 夜はまだ続く（結果待ち）
            decision.next_phase = None
        
        elif phase == "day":
            print("昼フェーズ")

            # 昼はまだ続く（結果待ち）
            decision.next_phase = None     

        else:
            decision.next_phase = "reveal"

        return GMGraphState(
            world_state=world_state,  # immutable
            decision=decision,  # working memory
        )


# 仮の GMGraph
gm_graph = DummyGMGraph()
