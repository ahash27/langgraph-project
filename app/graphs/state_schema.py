"""State schema for multi-agent workflows"""

from typing import TypedDict, Optional, Dict, Any, List


class AgentState(TypedDict, total=False):
    """
    Structured state schema for multi-agent system.
    
    This ensures type safety and clear data contracts between agents.
    """
    # Input
    input: str
    
    # Coordinator outputs
    plan: Dict[str, Any]
    next_agent: str
    coordinator_status: str
    
    # Processor outputs
    processed_output: Dict[str, Any]
    processor_status: str
    processor_confidence: float
    
    # Validator outputs
    validation_result: Dict[str, Any]
    is_valid: bool
    validator_status: str
    validation_score: float
    issues: List[str]
    
    # Final output
    final_output: Dict[str, Any]
    
    # Workflow control
    retry_count: int
    max_retries: int
    current_agent: str
    workflow_status: str
    
    # Observability
    execution_history: List[str]


class ToolExecutionState(TypedDict, total=False):
    """State for tool execution"""
    tool_name: str
    tool_input: Dict[str, Any]
    tool_output: Any
    tool_status: str
    error: Optional[str]
