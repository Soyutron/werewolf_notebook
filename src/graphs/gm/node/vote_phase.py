from src.core.types import GMGraphState, GameEvent, PlayerRequest


def vote_phase_node(state: GMGraphState) -> GMGraphState:
    """
    投票フェーズにおける GMGraph の進行ノード。

    責務:
    - 未投票プレイヤー（internal.vote_pending）が存在する場合、
      その全員に投票 request を出す
    - 全員の投票が完了していれば、次フェーズ（vote_result / end）への
      遷移意思を示す

    設計方針:
    - GMGraph は「判断のみ」を行い、state の実体更新は行わない
    - vote_pending の更新（投票完了者の除外）は GameSession 側の責務
    - このノードでは 1 step = 1 decision を厳守する
    """

    decision = state["decision"]
    internal = state["internal"]

    # 投票フェーズ開始イベント（最初の1回だけ）
    if not internal.vote_started:
        decision.events.append(
            GameEvent(
                event_type="vote_started",
                payload={},
            )
        )
        internal.vote_started = True
        # NOTE:
        # vote_started を True にするのは GameSession 側の責務

    # --- まだ投票していないプレイヤーがいる場合 ---
    if internal.vote_pending:
        # NOTE:
        # 投票フェーズでは request は「未投票者への投票要求」のみとするため、
        # decision.requests はここで完全に上書きする
        decision.requests = {
            player: PlayerRequest(
                request_type="vote",
                payload={},
            )
            for player in internal.vote_pending
        }

    # --- 全員の投票が完了している場合 ---
    else:
        # 次フェーズへの遷移意思のみを示す
        from src.core.types.phases import get_next_phase
        next_phase = get_next_phase(state["world_state"].phase, state["game_def"])
        
        if next_phase:
            decision.next_phase = next_phase

    return state
