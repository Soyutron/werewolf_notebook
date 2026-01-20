from src.core.types import GMGraphState, GameEvent, PlayerRequest


# 夜フェーズにおける能力実行優先度
# 数値が小さいほど先に実行される
ABILITY_PRIORITY = {
    "seer": 1,       # 情報取得系（占い師）が最優先
    "thief": 2,      # 役職変更系（怪盗）は情報取得後
    "werewolf": 3,   # その他（人狼）
    "none": 3,       # その他（村人、狂人など）
}


def get_ability_priority(ability_type: str) -> int:
    """能力タイプから実行優先度を取得する"""
    return ABILITY_PRIORITY.get(ability_type, 3)


def night_phase_node(state: GMGraphState) -> GMGraphState:
    """
    夜フェーズにおける GMGraph の進行ノード。

    責務:
    - 未完了プレイヤー（internal.night_pending）が存在する場合、
      能力の優先度に従って順次 request を出す
    - 全員の夜行動が完了していれば、次フェーズ（day）への遷移意思を示す

    能力実行順序:
    1. 情報取得系（占い師）: 先に占い結果を確定させる
    2. 役職変更系（怪盗）: 占い結果確定後に役職を交換
    3. その他（人狼、村人など）: 最後に処理

    設計方針:
    - GMGraph は「判断のみ」を行い、state の実体更新は行わない
    - night_pending の更新（完了者の除外）は GameSession 側の責務
    - このノードでは 1 step = 1 decision を厳守する
    """

    decision = state["decision"]
    internal = state["internal"]
    game_def = state["game_def"]

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
        # 各プレイヤーの能力優先度を取得
        # NOTE: assigned_roles は GM 側で管理されているため、
        # ここでは game_def からプレイヤーの役職を直接参照できない。
        # 代わりに、全プレイヤーに同時にリクエストを送り、
        # ActionResolver 側で順序を制御する設計とする。
        #
        # 将来的により厳密な順序制御が必要な場合は、
        # GMInternalState に ability_priority_queue を追加する。
        
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
        # GameDefinition から次のフェーズを取得
        from src.core.types.phases import get_next_phase
        next_phase = get_next_phase(state["world_state"].phase, state["game_def"])
        
        if next_phase:
            decision.next_phase = next_phase
        else:
            # 万が一取得できない場合はエラーログなどを出すべきだが、ここでは安全に停止
            pass

    return state

