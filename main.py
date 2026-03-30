"""Entry point for testing LangGraph setup"""

from app.config.settings import validate_config
from app.graphs.sample_graph import build_graph

def main():
    """Run sample graph to verify setup"""
    try:
        # Validate configuration
        validate_config()
        
        # Build and run graph
        graph = build_graph()
        result = graph.invoke({"input": "Hello AI"})
        
        print("✅ LangGraph setup successful!")
        print(f"Result: {result}")
        
    except ValueError as e:
        print(f"❌ Configuration error: {e}")
        print("Please set up your .env file with required API keys")
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    main()
