# src/graphs/gm/node/log_summarize_node.py
"""
GM用ログ要約ノード

責務:
- public_events の差分を取得
- 差分要約を実行
- internal.log_summary と internal.last_summarized_event_index を更新
"""

from src.core.types import GMGraphState


def gm_log_summarize_node(state: GMGraphState) -> GMGraphState:
    """
    GM用ログ要約ノード。
    
    gm_generate ノードの前に実行され、
    public_events を要約して internal.log_summary に格納する。
    """
    # Lazy import to avoid circular import
    from src.game.log_summarizer import get_log_summarizer
    
    print("[gm_log_summarize_node] Starting log summarization...")
    
    world = state["world_state"]
    internal = state["internal"]
    
    # GM は public_events + pending_events を観測する
    all_events = world.public_events + world.pending_events
    
    # 要約を実行
    summarizer = get_log_summarizer()
    new_summary, new_cursor = summarizer.summarize_incremental(
        events=all_events,
        previous_summary=internal.log_summary,
        last_index=internal.last_summarized_event_index,
    )
    
    # internal を更新
    internal.log_summary = new_summary
    internal.last_summarized_event_index = new_cursor
    
    print(f"[gm_log_summarize_node] Summary updated (cursor: {new_cursor})")
    
    return state
