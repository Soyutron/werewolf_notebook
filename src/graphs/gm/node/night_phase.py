from src.core.types import GMGraphState, GameEvent, PlayerRequest


def night_phase_node(state: GMGraphState) -> GMGraphState:
    """
    夜フェーズにおける GMGraph の進行ノード。

    責務:
    - 未完了プレイヤー（internal.night_pending）が存在する場合、
      その全員に夜行動の request を出す
    - 全員の夜行動が完了していれば、次フェーズ（day）への遷移意思を示す

    設計方針:
    - GMGraph は「判断のみ」を行い、state の実体更新は行わない
    - night_pending の更新（完了者の除外）は GameSession 側の責務
    - このノードでは 1 step = 1 decision を厳守する
    """

    decision = state["decision"]
    internal = state["internal"]

    # 夜フェーズ開始イベント（最初の1回だけ）
    if not internal.night_started:
        decision.events.append(
            GameEvent(
                event_type="night_started",
                payload={},
            )
        )
        internal.night_started = True
        # NOTE:
        # night_started を True にするのは GameSession 側の責務

    # --- 夜行動が未完了のプレイヤーがいる場合 ---
    if internal.night_pending:
        # NOTE:
        # 夜フェーズでは request は「未完了者への夜行動要求」のみとするため、
        # decision.requests はここで完全に上書きする
        decision.requests = {
            player: PlayerRequest(
                request_type="use_ability",
                payload={},
            )
            for player in internal.night_pending
        }

    # --- 全員の夜行動が完了している場合 ---
    else:
        # 次フェーズへの遷移意思のみを示す
        # 実際の phase 更新は GameSession の dispatch が行う
        decision.next_phase = "day"

    return state
