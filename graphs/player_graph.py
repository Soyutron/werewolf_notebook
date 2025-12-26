from langgraph.graph import StateGraph, END
from core.nodes import make_handle_event, decide_action
from core.types import PlayerState

def create_player_graph(llm):
    """
    Creates and compiles the player graph with the given LLM dependency.
    """
    # Create the node function with the injected LLM
    handle_event = make_handle_event(llm)

    player_graph = StateGraph(PlayerState)

    player_graph.add_node("handle_event", handle_event)
    player_graph.add_node("decide_action", decide_action)

    player_graph.set_entry_point("handle_event")
    player_graph.add_edge("handle_event", "decide_action")
    player_graph.add_edge("decide_action", END)

    return player_graph.compile()