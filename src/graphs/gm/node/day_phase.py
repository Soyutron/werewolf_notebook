from src.core.types import GMGraphState, GameEvent, PlayerRequest
from src.game.gm.gm_comment_generator import gm_comment_generator
from src.game.gm.gm_maturity_judge import gm_maturity_judge


def day_phase_node(state: GMGraphState) -> GMGraphState:
    """
    昼フェーズにおける GMGraph の進行ノード。

    責務:
    - 昼フェーズ開始イベントを最初の1回だけ送出する
    - 状況に応じて次の発言者を1人指名する
    - 議論が成熟、または一定回数を超えた場合は vote フェーズへの遷移意思を示す

    設計方針:
    - GMGraph は「判断のみ」を行う
    - 発言回数・履歴更新は GameSession 側の責務
    - 1 step = 1 decision を厳守する
    """
    public_events = state["world_state"].public_events
    pending_events = state["world_state"].pending_events
    context = public_events + pending_events
    players = state["world_state"].players
    decision = state["decision"]
    internal = state["internal"]

    # -------------------------
    # 昼フェーズ開始イベント
    # -------------------------
    if not internal.day_started:
        decision.events.append(
            GameEvent(
                event_type="day_started",
                payload={},
            )
        )
        internal.day_started = True

    # -------------------------
    # 議論終了判定
    # -------------------------
    # ハードリミット（安全弁）
    if internal.discussion_turn >= internal.max_discussion_turn:
        decision.next_phase = "vote"
        return state

    if internal.discussion_turn >= internal.min_discussion_turn:
        # ★ 成熟判定（ソフト判定）
        maturity = gm_maturity_judge.judge(
            public_events=context,
        )

        print(maturity)
        print(decision.next_phase)

        if maturity and maturity.is_mature:
            decision.events.append(
                GameEvent(
                    event_type="gm_comment",
                    payload={
                        "text": maturity.reason,
                        "speaker": "GM",
                    },
                )
            )
            print("mature")
            decision.next_phase = "vote"
            return state

    # -------------------------
    # 次の発言者を指名
    # -------------------------
    gm_comment = gm_comment_generator.generate(
        public_events=context,
        players=players,
    )
    speaker = gm_comment.speaker
    text = gm_comment.text
    internal.discussion_turn += 1

    # ★ GMコメント（全員に公開）
    decision.events.append(
        GameEvent(
            event_type="gm_comment",
            payload={
                "text": text,
                "speaker": speaker,
            },
        )
    )

    decision.requests = {
        speaker: PlayerRequest(
            request_type="speak",
            payload={},
        )
    }

    return state
