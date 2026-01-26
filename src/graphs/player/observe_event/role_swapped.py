"""
役職交換イベントのハンドラ

怪盗が役職交換を行った際に、GM から送信される role_swapped イベントを処理し、
怪盗自身の memory.self_role を更新する。
"""

from src.core.types import PlayerState, RoleName


def handle_role_swapped(state: PlayerState) -> PlayerState:
    """
    役職交換結果を受け取り、プレイヤーの役職情報を更新するノード。

    設計方針:
    - role_swapped は怪盗本人にのみ届く「確定情報」
    - memory.self_role を新しい役職に更新する
    - 行動は発生しない（output は None）
    
    注意:
    - 交換後の勝敗判定は新しい役職に基づく
    - 占い結果は「占い実行時点」の役職を返すため、
      交換により最終役職と一致しない可能性がある（仕様通り）
    """

    event = state["input"].event
    if event is None or event.event_type != "role_swapped":
        return state

    new_role: RoleName = event.payload["new_role"]
    target: str = event.payload["target"]

    memory = state["memory"]

    # -------------------------
    # 1. 自分の役職を更新
    # -------------------------
    # 怪盗は交換後の役職として扱われる
    old_role = memory.self_role
    memory.self_role = new_role
    
    print(f"[DEBUG] handle_role_swapped: {memory.self_name} role changed from {old_role} to {new_role} (swapped with {target})")

    # -------------------------
    # 2. 観測イベントの保存
    # -------------------------
    # role_swapped は private event だが、
    # 「自分が観測した事実」としては保存してよい
    memory.observed_events.append(event)

    # -------------------------
    # 3. 役職確率分布の更新（オプション）
    # -------------------------
    # 自分の役職は確定しているので role_beliefs[self_name] は更新不要
    # （self_role が真実情報として PlayerMemory に保持されているため）
    # 
    # 交換相手の役職は「怪盗（旧：自分）」になったことを知っている
    # しかし「怪盗」という役職は交換後に存在しなくなるため、
    # 単純に確率分布を更新するのは複雑になる。
    # ここでは最小限の実装として、イベント保存のみとする。

    # 行動はしない
    state["output"] = None
    return state
