from src.llm.ollama import LangChainSpeechEvaluator
from src.graphs.player_graph import create_player_graph

def main():
    print("Initializing components...")
    
    # Initialize LLM (using default settings for now)
    # Note: Requires a running Ollama instance with llama3 or similar
    # For testing without Ollama, we might want to mock this or ensure 
    # the user has it set up. We'll try to init it.
    try:
        llm = LangChainSpeechEvaluator()
        print("LLM initialized.")
    except Exception as e:
        print(f"Failed to initialize LLM: {e}")
        return

    # Create the graph
    try:
        player_graph = create_player_graph(llm)
        print("Player graph compiled successfully.")
    except Exception as e:
        print(f"Failed to create graph: {e}")
        return

    # Basic structure check (optional)
    print("Graph structure verified.")

if __name__ == "__main__":
    main()
