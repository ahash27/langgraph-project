"""Multi-agent workflow graph with dynamic routing."""

from langgraph.graph import END, StateGraph

from app.agents.coordinator_agent import CoordinatorAgent
from app.agents.processor_agent import ProcessorAgent
from app.agents.validator_agent import ValidatorAgent
from app.graphs.state_schema import AgentState
from app.utils.logger import log_routing_decision


def route_after_validator(state: AgentState) -> str:
    """
    Dynamic routing after validator.
    
    Routes to:
    - processor: if validation failed and retries available
    - end: if validation passed or max retries reached
    """
    is_valid = state.get("is_valid", False)
    retry_count = state.get("retry_count", 0)
    max_retries = state.get("max_retries", 3)
    
    if not is_valid and retry_count < max_retries:
        reason = f"validation failed, retry {retry_count}/{max_retries}"
        log_routing_decision("validator", "processor", reason)
        return "processor"  # Loop back for retry
    else:
        reason = "validation passed" if is_valid else "max retries reached"
        log_routing_decision("validator", "end", reason)
        return "end"


def route_after_coordinator(state: AgentState) -> str:
    """
    Dynamic routing after coordinator.
    
    COORDINATOR DECIDES - reads from plan's next_agent field.
    This is TRUE agent autonomy.
    """
    plan = state.get("plan", {})
    
    # Coordinator decides next agent (stored in plan)
    next_agent = plan.get("next_agent", "processor")
    
    return next_agent


def build_multi_agent_graph():
    """
    Build a multi-agent workflow graph with conditional routing.
    
    Flow: 
    - Coordinator → [decides next agent]
    - Processor → Validator
    - Validator → Processor (if validation fails, retry loop)
    - Validator → END (if validation passes or max retries)
    
    Returns:
        Compiled LangGraph workflow with dynamic routing
    """
    # Initialize agents
    coordinator = CoordinatorAgent()
    processor = ProcessorAgent()
    validator = ValidatorAgent()
    
    # Build graph
    builder = StateGraph(AgentState)
    
    # Add agent nodes
    builder.add_node("coordinator", coordinator)
    builder.add_node("processor", processor)
    builder.add_node("validator", validator)
    
    # Define workflow with conditional routing
    builder.set_entry_point("coordinator")
    
    # Coordinator decides next agent (TRUE AUTONOMY)
    builder.add_conditional_edges(
        "coordinator",
        route_after_coordinator,
        {
            "processor": "processor",
            "validator": "validator",  # Could skip processor for simple tasks
            "end": END
        }
    )
    
    # Processor → Validator (always)
    builder.add_edge("processor", "validator")
    
    # Validator → Processor (retry loop) OR END
    builder.add_conditional_edges(
        "validator",
        route_after_validator,
        {
            "processor": "processor",
            "end": END
        }
    )
    
    return builder.compile()
