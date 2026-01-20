# src/game/gm/nodes/day_phase_router.py

from src.core.types import GameEvent, GMGraphState
from src.game.gm.gm_maturity_judge import gm_maturity_judge


def day_phase_router_node(state: GMGraphState) -> str:
    """
    昼フェーズを継続するか、投票フェーズへ進むかを判定する Router ノード。

    戻り値:
    - "continue": 議論継続
    - "vote": 投票フェーズへ遷移

    判定ルール:
    1. ハードリミット（最大ターン数）に達したら即 vote
    2. 最小ターン数を超えていれば成熟判定を行う
       - 成熟していれば GM コメントを追加して vote
       - 未成熟なら continue
    """

    internal = state["internal"]
    world = state["world_state"]
    decision = state["decision"]

    public_events = world.public_events

    # -----------------------------
    # 1. ハードリミット判定
    # -----------------------------
    if internal.discussion_turn >= internal.max_discussion_turn:
        # 次のフェーズへ遷移する意思を示す
        from src.core.types.phases import get_next_phase
        next_phase = get_next_phase(world.phase, state["game_def"])
        decision.next_phase = next_phase
        return "vote"

    # -----------------------------
    # 2. ソフト判定（成熟度）
    # -----------------------------
    if internal.discussion_turn >= internal.min_discussion_turn:
        maturity = gm_maturity_judge.judge(public_events=public_events)

        if maturity is not None and maturity.is_mature:
            decision.events.append(
                GameEvent(
                    event_type="gm_comment",
                    payload={
                        "speaker": "GM",
                        "text": maturity.reason,
                    },
                )
            )
            
            # 次のフェーズへ遷移する意思を示す
            from src.core.types.phases import get_next_phase
            next_phase = get_next_phase(world.phase, state["game_def"])
            decision.next_phase = next_phase
            
            # グラフエッジの識別子として "vote" を返すが、意味としては "end_day_loop"
            # gm_graph.py で "vote": END になっているため、これで day ループが終了する
            return "vote"

    # -----------------------------
    # 3. 継続
    # -----------------------------
    return "continue"
