"""Multi-agent workflow graph with dynamic routing"""

from langgraph.graph import StateGraph, END
from app.agents.coordinator_agent import CoordinatorAgent
from app.agents.processor_agent import ProcessorAgent
from app.agents.validator_agent import ValidatorAgent
from app.nodes.fetch_trends_node import FetchTrendsNode
from app.nodes.generate_posts_node import generate_posts
from app.nodes.human_approval_node import HumanApprovalNode
from app.nodes.publish_post_node import publish_post
from app.utils.logger import log_routing_decision
from app.graphs.state_schema import AgentState


def route_after_validator(state: AgentState) -> str:
    """
    Dynamic routing after validator.
    
    Routes to:
    - processor: if validation failed and retries available
    - publish_post: if validation passed and publish approval exists
    - end: otherwise
    """
    is_valid = state.get("is_valid", False)
    retry_count = state.get("retry_count", 0)
    max_retries = state.get("max_retries", 3)
    
    if not is_valid and retry_count < max_retries:
        reason = f"validation failed, retry {retry_count}/{max_retries}"
        log_routing_decision("validator", "processor", reason)
        return "processor"  # Loop back for retry

    approved = bool(state.get("approved_for_publish"))
    draft = (state.get("approved_content") or state.get("publish_draft_text") or "").strip()
    if is_valid and approved and draft:
        log_routing_decision("validator", "publish_post", "validated and approved for publish")
        return "publish_post"

    reason = "validation passed" if is_valid else "max retries reached"
    log_routing_decision("validator", "end", reason)
    return "end"


def route_after_coordinator(state: AgentState) -> str:
    """
    Dynamic routing after coordinator.
    
    Routes to:
    - fetch_trends: if intent is trends-related
    - processor: for generic processing
    - validator: for simple validation-only tasks
    - end: if no processing needed
    """
    plan = state.get("plan", {})
    
    # Check intent for trends
    intent = plan.get("intent", "")
    if intent == "trends":
        log_routing_decision("coordinator", "fetch_trends", "trends intent detected")
        return "fetch_trends"
    
    # Coordinator decides next agent (stored in plan)
    next_agent = plan.get("next_agent") or state.get("next_agent", "processor")
    
    return next_agent


def route_after_generate_posts(state: AgentState) -> str:
    """Route drafts to human approval for trends, otherwise straight to validator."""
    plan = state.get("plan", {})
    intent = plan.get("intent", "")
    if intent == "trends":
        return "human_approval"
    return "validator"


def build_multi_agent_graph():
    """
    Build a multi-agent workflow graph with conditional routing.
    
    Flow: 
    - Coordinator → [decides next agent]
    - fetch_trends → generate_posts → human_approval → Validator (for trends requests)
    - Processor → generate_posts → Validator (for generic requests)
    - Validator → Processor (if validation fails, retry loop)
    - Validator → END (if validation passes or max retries)
    - human_approval can route back to fetch_trends on reject
    
    Returns:
        Compiled LangGraph workflow with dynamic routing and human approval
    """
    # Initialize agents and nodes with dependency injection
    coordinator = CoordinatorAgent()
    processor = ProcessorAgent()
    validator = ValidatorAgent()
    fetch_trends = FetchTrendsNode(processor)  # Inject processor dependency
    human_approval = HumanApprovalNode()
    
    # Build graph
    builder = StateGraph(AgentState)
    
    # Add agent nodes
    builder.add_node("coordinator", coordinator)
    builder.add_node("processor", processor)
    builder.add_node("validator", validator)
    builder.add_node("fetch_trends", fetch_trends)
    builder.add_node("generate_posts", generate_posts)
    builder.add_node("human_approval", human_approval)
    builder.add_node("publish_post", publish_post)
    
    # Define workflow with conditional routing
    builder.set_entry_point("coordinator")
    
    # Coordinator decides next agent (TRUE AUTONOMY)
    builder.add_conditional_edges(
        "coordinator",
        route_after_coordinator,
        {
            "fetch_trends": "fetch_trends",  # NEW: dedicated trends node
            "processor": "processor",
            "validator": "validator",  # Could skip processor for simple tasks
            "end": END
        }
    )
    
    # Trends path: fetch and then generate three variants
    builder.add_edge("fetch_trends", "generate_posts")

    # Generic path: process then generate three variants
    builder.add_edge("processor", "generate_posts")

    # Draft routing: trends require human approval, generic goes to validator.
    builder.add_conditional_edges(
        "generate_posts",
        route_after_generate_posts,
        {
            "human_approval": "human_approval",
            "validator": "validator",
        },
    )
    
    # Human approval → validator (always after approve/edit)
    # Note: human_approval can return Command(goto="fetch_trends") on reject.
    builder.add_edge("human_approval", "validator")
    
    # Validator → Processor (retry loop), publish_post, or END
    builder.add_conditional_edges(
        "validator",
        route_after_validator,
        {
            "processor": "processor",
            "publish_post": "publish_post",
            "end": END
        }
    )
    builder.add_edge("publish_post", END)
    
    return builder.compile()
