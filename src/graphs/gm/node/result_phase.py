from collections import Counter
from src.core.types import GMGraphState, GameEvent, GameResult
from src.core.types.roles import RoleName

def result_phase_node(state: GMGraphState) -> GMGraphState:
    """
    結果フェーズにおける GMGraph の進行ノード。

    責務:
    - 投票結果の集計
    - 処刑されるプレイヤーの決定
    - 勝敗判定
    - GameResult の生成
    """
    decision = state["decision"]
    internal = state["internal"]
    world_state = state["world_state"]
    assigned_roles = state["assigned_roles"]

    # 1. 投票の集計
    votes = internal.votes
    if not votes:
        # 投票がない（異常系だが、全員放棄など）
        # ワンナイト人狼では通常ありえないが、処刑なしとする
        executed_players = []
    else:
        vote_counts = Counter(votes.values())
        max_votes = max(vote_counts.values())
        
        # 最多得票者を全員取得（同数なら全員処刑）
        executed_players = [
            player for player, count in vote_counts.items()
            if count == max_votes
        ]

    # 2. 勝敗判定
    # ルール:
    # - 処刑されたプレイヤーの中に「人狼」がいれば、村人陣営の勝利
    # - 人狼が一人も処刑されなければ、人狼陣営の勝利
    
    # 処刑された人たちの役職を確認
    executed_roles = [assigned_roles[p] for p in executed_players]
    
    # 人狼が含まれているか？
    werewolf_executed = "werewolf" in executed_roles
    
    if werewolf_executed:
        winner = "village"
    else:
        winner = "werewolf"

    # 3. GameResult の作成
    game_result = GameResult(
        winner=winner,
        executed_players=executed_players,
        roles=assigned_roles,
    )
    
    # world_state.result は session.dispatch で更新されるが、
    # ここでは Event として通知するか、あるいは直接 state を書き換える命令を出すか。
    # PhaseRunner.run_result_step -> session.dispatch -> dispatcher
    # Dispatcher が GameDecision をどう処理するか？
    # Decision には "result" フィールドがない。
    # 
    # しかし GameSession は GMGraphState["world_state"] を採用する。
    # なので、ここで world_state.result を設定してしまえばよい。
    # GMGraph は "world_state を書き換えない" 原則があるが、
    # 返り値の GMGraphState["world_state"] は "次の状態" として返される。
    
    # world_state は immutable 扱いだが、新しいインスタンスを作るか、
    # deepcopy されている前提で変更するか。
    # LangGraph の state は通常 dict で回される。
    # ここでは world_state オブジェクト（Pydantic）なので、copyが良い。
    
    new_world_state = world_state.model_copy()
    new_world_state.result = game_result
    state["world_state"] = new_world_state

    # 4. イベント通知
    # 結果発表イベント
    decision.events.append(
        GameEvent(
            event_type="game_end",
            payload={
                "winner": winner,
                "executed": executed_players,
                "roles": assigned_roles,
            },
        )
    )

    # 次のフェーズはなし（終了）
    decision.next_phase = None

    return state
