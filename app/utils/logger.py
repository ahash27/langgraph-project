"""Observability and logging utilities for multi-agent system"""

import json
from typing import Dict
from app.graphs.state_schema import AgentState, JSONValue
from datetime import datetime


def log_agent_step(agent_name: str, state: AgentState, action: str = "execute"):
    """
    Log agent execution step for observability.
    
    Args:
        agent_name: Name of the agent
        state: Current state (will extract relevant fields)
        action: Action being performed (execute, route, retry, etc.)
    """
    timestamp = datetime.now().isoformat()
    
    # Extract relevant state info (avoid logging entire state)
    relevant_info = {
        "retry_count": state.get("retry_count", 0),
        "confidence": state.get("processor_confidence"),
        "is_valid": state.get("is_valid"),
        "next_agent": state.get("next_agent"),
        "current_agent": state.get("current_agent")
    }
    
    # Remove None values
    relevant_info = {k: v for k, v in relevant_info.items() if v is not None}
    
    print(f"[{timestamp}] [{agent_name.upper()}] {action} → {json.dumps(relevant_info)}")


def log_routing_decision(from_agent: str, to_agent: str, reason: str = ""):
    """
    Log routing decision for debugging.
    
    Args:
        from_agent: Source agent
        to_agent: Destination agent
        reason: Reason for routing decision
    """
    timestamp = datetime.now().isoformat()
    reason_str = f" (reason: {reason})" if reason else ""
    print(f"[{timestamp}] [ROUTING] {from_agent} → {to_agent}{reason_str}")


def log_tool_usage(agent_name: str, tool_name: str, success: bool = True):
    """
    Log tool usage by agents.
    
    Args:
        agent_name: Agent using the tool
        tool_name: Tool being used
        success: Whether tool execution succeeded
    """
    timestamp = datetime.now().isoformat()
    status = "✓" if success else "✗"
    print(f"[{timestamp}] [{agent_name.upper()}] Tool: {tool_name} {status}")


def log_workflow_summary(state: AgentState):
    """
    Log workflow execution summary.
    
    Args:
        state: Final state after workflow completion
    """
    print("\n" + "=" * 70)
    print("WORKFLOW EXECUTION SUMMARY")
    print("=" * 70)
    
    history = state.get("execution_history", [])
    if history:
        print(f"Execution Path: {' → '.join(history)}")
    
    print(f"Total Retries: {state.get('retry_count', 0)}")
    print(f"Final Status: {state.get('workflow_status', 'completed')}")
    print(f"Validation: {'✓ Passed' if state.get('is_valid') else '✗ Failed'}")
    
    if state.get("issues"):
        print(f"Issues: {', '.join(state['issues'])}")
    
    print("=" * 70 + "\n")
