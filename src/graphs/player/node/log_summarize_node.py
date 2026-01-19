# src/graphs/player/node/log_summarize_node.py
"""
プレイヤー用ログ要約ノード

責務:
- 前回の要約以降に追加されたイベントを取得
- 差分要約を実行
- memory.log_summary と memory.last_summarized_event_index を更新
"""

from src.core.types.player import PlayerState


def log_summarize_node(state: PlayerState) -> PlayerState:
    """
    ログを要約するノード。
    
    発言生成の直前に実行され、
    observed_events を要約して log_summary に格納する。
    """
    # Lazy import to avoid circular import
    from src.game.log_summarizer import get_log_summarizer
    
    print("[log_summarize_node] Starting log summarization...")
    
    memory = state["memory"]
    
    # 要約を実行
    summarizer = get_log_summarizer()
    new_summary, new_cursor = summarizer.summarize_incremental(
        events=memory.observed_events,
        previous_summary=memory.log_summary,
        last_index=memory.last_summarized_event_index,
    )
    
    # memory を更新
    memory.log_summary = new_summary
    memory.last_summarized_event_index = new_cursor
    
    print(f"[log_summarize_node] Summary updated (cursor: {new_cursor})")
    
    return state
