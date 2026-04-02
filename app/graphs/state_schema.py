"""State schema for multi-agent workflows."""

from typing import TypedDict, Optional, Dict, List, Union


# JSON-compatible value types
JSONValue = Union[str, int, float, bool, None, Dict[str, "JSONValue"], List["JSONValue"]]


class Metadata(TypedDict, total=False):
    """Metadata for agent outputs"""
    status: str
    tools_used: List[str]
    data_source: str
    steps_completed: int


class AgentPlan(TypedDict, total=False):
    """Plan created by coordinator agent"""
    task: str
    complexity: float
    requires_tools: List[str]
    steps: List[str]
    intent: str


class TrendItem(TypedDict, total=False):
    """Individual trend item"""
    topic: str
    rank: int
    score: Optional[float]
    source: str
    link: Optional[str]
    description: str
    related_queries: List[str]
    related_queries_error: Optional[str]


class TrendsData(TypedDict, total=False):
    """Trends data from tools"""
    source: str
    status: str
    region: str
    trends: List[TrendItem]
    count: int
    error: Optional[str]
    sources_queried: int
    sources_successful: int
    raw_sources: List[Dict[str, JSONValue]]


class ProcessedOutput(TypedDict, total=False):
    """Output from processor agent"""
    original_input: str
    intent: str
    result: str
    trends_data: TrendsData
    transformed_input: str
    plan_executed: str
    error: Optional[str]
    error_details: Optional[str]
    metadata: Metadata


class ValidationResult(TypedDict, total=False):
    """Output from validator agent"""
    is_valid: bool
    confidence: float
    issues: List[str]
    suggestions: List[str]
    metadata: Metadata


class AgentState(TypedDict, total=False):
    """Shared notebook for all agents in the multi-agent graph."""

    schema_version: Literal["1.0"]

    # Input
    input: str
    region: str
    
    # Coordinator outputs
    plan: AgentPlan
    next_agent: str
    coordinator_status: str

    # Processor outputs
    processed_output: ProcessedOutput
    processor_status: str
    processor_confidence: float

    # Validator outputs
    validation_result: ValidationResult
    is_valid: bool
    validator_status: str
    validation_score: float

    # Final output
    final_output: ProcessedOutput
    
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
    tool_input: Dict[str, JSONValue]
    tool_output: JSONValue
    tool_status: str
    error: Optional[str]
