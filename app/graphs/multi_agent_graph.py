"""Multi-agent workflow graph with dynamic routing."""

from langgraph.graph import END, StateGraph

from app.agents.coordinator_agent import CoordinatorAgent
from app.agents.processor_agent import ProcessorAgent
from app.agents.validator_agent import ValidatorAgent
from app.graphs.state_schema import AgentState
from app.nodes.generate_posts_node import generate_posts
from app.nodes.publish_post_node import publish_post
from app.utils.logger import log_routing_decision


def route_after_validator(state: AgentState) -> str:
    """
    Dynamic routing after validator.

    Routes to:
    - processor: if validation failed and retries available
    - publish_post: if validation passed, approved_for_publish, and draft text present
    - end: otherwise
    """
    is_valid = state.get("is_valid", False)
    retry_count = state.get("retry_count", 0)
    max_retries = state.get("max_retries", 3)

    if not is_valid and retry_count < max_retries:
        reason = f"validation failed, retry {retry_count}/{max_retries}"
        log_routing_decision("validator", "processor", reason)
        return "processor"

    approved = bool(state.get("approved_for_publish"))
    draft = (state.get("publish_draft_text") or "").strip()
    if is_valid and approved and draft:
        log_routing_decision("validator", "publish_post", "approved draft, publishing")
        return "publish_post"

    reason = "validation passed" if is_valid else "max retries reached"
    if is_valid and approved and not draft:
        reason = "approved but no publish_draft_text"
    log_routing_decision("validator", "end", reason)
    return "end"


def route_after_coordinator(state: AgentState) -> str:
    """
    Dynamic routing after coordinator.
    
    COORDINATOR DECIDES - reads from top-level next_agent field.
    This is TRUE agent autonomy.
    """
    return state.get("next_agent", "processor")


def build_multi_agent_graph():
    """
    Build a multi-agent workflow graph with conditional routing.
    
    Flow:
    - Coordinator → [decides next agent]
    - Processor → generate_posts → Validator
    - Validator → Processor (if validation fails, retry loop)
    - Validator → publish_post (if valid + approved_for_publish + draft text)
    - Validator → END (otherwise)
    - publish_post → END
    
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
    builder.add_node("generate_posts", generate_posts)
    builder.add_node("validator", validator)
    builder.add_node("publish_post", publish_post)

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
    
    # Processor → generate_posts → Validator
    builder.add_edge("processor", "generate_posts")
    builder.add_edge("generate_posts", "validator")
    
    # Validator → Processor (retry loop) OR END
    builder.add_conditional_edges(
        "validator",
        route_after_validator,
        {
            "processor": "processor",
            "publish_post": "publish_post",
            "end": END,
        },
    )
    builder.add_edge("publish_post", END)

    return builder.compile()
