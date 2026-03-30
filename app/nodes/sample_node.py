"""Sample node demonstrating basic LangGraph node structure"""

def hello_node(state: dict) -> dict:
    """
    Basic processing node that transforms input
    
    Args:
        state: Current graph state with 'input' key
        
    Returns:
        Updated state with 'message' key
    """
    input_text = state.get("input", "")
    return {"message": f"{input_text} processed by LangGraph"}
