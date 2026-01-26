from collections import Counter
from typing import List

from src.core.types import GMGraphState, GameEvent, GameResult
from src.core.types.roles import RoleName
from src.core.types.player import PlayerName

def result_phase_node(state: GMGraphState) -> GMGraphState:
    """
    結果フェーズにおける GMGraph の進行ノード。

    責務:
    - 投票結果の集計（ワンナイト人狼ルールに基づく）
    - 勝敗判定
    - GameResult の生成
    - 結果開示イベントの発行
    """
    decision = state["decision"]
    internal = state["internal"]
    world_state = state["world_state"]
    game_def = state["game_def"]
    assigned_roles = state["assigned_roles"]

    # 1. 投票の集計
    votes = internal.votes
    executed_players: List[PlayerName] = []

    if not votes:
        # 投票がない場合は処刑なし
        executed_players = []
    else:
        vote_counts = Counter(votes.values())
        max_votes = max(vote_counts.values())
        
        # ワンナイト人狼ルール:
        # 最多得票数が1票の場合は「処刑なし」（全員が別の人の場合など）
        # それ以外の場合は最多得票者全員が処刑される
        if max_votes == 1:
            executed_players = []
        else:
            executed_players = [
                player for player, count in vote_counts.items()
                if count == max_votes
            ]

    # 2. 勝敗判定
    # 処刑されたプレイヤーの中に人狼がいるか確認
    executed_werewolves = []
    for player in executed_players:
        role_name = assigned_roles.get(player)
        if role_name:
            role_def = game_def.roles.get(role_name)
            # day_side が werewolf のキャラを人狼とみなす
            if role_def and role_def.day_side == "werewolf":
                executed_werewolves.append(player)
    
    # 場に人狼がいるか確認
    active_werewolves = []
    for player, role_name in assigned_roles.items():
        role_def = game_def.roles.get(role_name)
        if role_def and role_def.day_side == "werewolf":
            active_werewolves.append(player)
            
    winner = "werewolf" # デフォルト
    
    if executed_werewolves:
        # 人狼が処刑されれば村人勝利
        winner = "village"
    else:
        # 人狼が処刑されていない場合
        if len(executed_players) > 0:
            # 誰かが処刑されたが、人狼ではない -> 人狼勝利
            winner = "werewolf"
        else:
            # 誰も処刑されていない場合
            if len(active_werewolves) == 0:
                # 人狼が不在で平和村（処刑なし） -> 村人勝利
                winner = "village"
            else:
                # 人狼がいるのに処刑なし -> 人狼勝利
                winner = "werewolf"

    # 3. GameResult の作成
    game_result = GameResult(
        winner=winner,
        executed_players=executed_players,
        roles=assigned_roles,
    )
    
    # world_state の更新
    # GMGraph は本来 world_state を書き換えないが、Resultフェーズは例外的に結果を確定させる
    new_world_state = world_state.model_copy()
    new_world_state.result = game_result
    state["world_state"] = new_world_state

    # 4. イベント通知
    decision.events.append(
        GameEvent(
            event_type="game_end",
            payload={
                "winner": winner,
                "executed_players": executed_players,
                "roles": assigned_roles,
            },
        )
    )

    # 次のフェーズはなし（終了）
    decision.next_phase = None

    return state
