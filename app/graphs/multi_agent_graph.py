"""Multi-agent workflow graph with dynamic routing"""

from langgraph.graph import StateGraph, END
from app.agents.coordinator_agent import CoordinatorAgent
from app.agents.processor_agent import ProcessorAgent
from app.agents.validator_agent import ValidatorAgent
from app.nodes.fetch_trends_node import FetchTrendsNode
from app.nodes.human_approval_node import HumanApprovalNode
from app.utils.logger import log_routing_decision
from app.graphs.state_schema import AgentState


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
    next_agent = plan.get("next_agent", "processor")
    
    return next_agent


def build_multi_agent_graph():
    """
    Build a multi-agent workflow graph with conditional routing.
    
    Flow: 
    - Coordinator → [decides next agent]
    - fetch_trends → human_approval (NEW) → Validator (for trends requests)
    - Processor → Validator (for generic requests)
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
    builder = StateGraph(dict)
    
    # Add agent nodes
    builder.add_node("coordinator", coordinator)
    builder.add_node("processor", processor)
    builder.add_node("validator", validator)
    builder.add_node("fetch_trends", fetch_trends)
    builder.add_node("human_approval", human_approval)
    
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
    
    # fetch_trends → human_approval (NEW: human-in-the-loop)
    builder.add_edge("fetch_trends", "human_approval")
    
    # human_approval → validator (after approval/edit)
    # Note: human_approval can also return Command(goto="fetch_trends") on reject
    builder.add_edge("human_approval", "validator")
    
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
