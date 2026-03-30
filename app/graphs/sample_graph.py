"""Sample graph demonstrating basic LangGraph workflow"""

from langgraph.graph import StateGraph, END
from app.nodes.sample_node import hello_node

def build_graph():
    """
    Build a simple graph with one node
    
    Returns:
        Compiled LangGraph workflow
    """
    builder = StateGraph(dict)
    
    # Add nodes
    builder.add_node("hello", hello_node)
    
    # Define flow
    builder.set_entry_point("hello")
    builder.add_edge("hello", END)
    
    return builder.compile()
