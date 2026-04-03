"""Fetch trends node - dedicated LangGraph node for trends pipeline"""

from typing import List, Dict, Union
from app.agents.processor_agent import ProcessorAgent
from app.graphs.state_schema import AgentState, TrendItem, Metadata, JSONValue
from app.utils.logger import log_agent_step


class FetchTrendsNode:
    """
    Dedicated LangGraph node for fetching and processing trends.
    
    This node extracts the trends pipeline from ProcessorAgent into
    a reusable graph node for better separation of concerns.
    
    Responsibilities:
    - Fetch raw trends from aggregator
    - Apply relevance filtering
    - Deduplicate against recent trends
    - Limit to max results
    - Return immutable state updates
    
    Architecture:
    - Uses dependency injection for ProcessorAgent (testable, decoupled)
    - Returns new state dict (immutable pattern)
    - Provides clean separation between orchestration and execution
    """
    
    def __init__(self, processor: ProcessorAgent):
        """
        Initialize with processor agent via dependency injection.
        
        Args:
            processor: ProcessorAgent instance for pipeline reuse
            
        Benefits:
        - Loose coupling (can swap implementations)
        - Easier testing (can inject mocks)
        - Explicit dependencies (no hidden coupling)
        """
        self.processor = processor
    
    def __call__(self, state: AgentState) -> AgentState:
        """
        Execute trends fetching pipeline.
        
        Args:
            state: Agent state containing region and other params
            
        Returns:
            New state dict with trends and metadata (immutable)
        """
        log_agent_step("fetch_trends_node", state, "start")
        
        try:
            # Use existing pipeline from ProcessorAgent
            trends_data = self.processor.fetch_trends(state)
            
            # Extract trends with proper type validation (no type: ignore)
            trends_raw = trends_data.get("trends")
            trends: List[TrendItem] = trends_raw if isinstance(trends_raw, list) else []
            
            # Extract sources with proper type validation
            sources_raw = trends_data.get("raw_sources") or trends_data.get("sources")
            sources: List[Dict[str, JSONValue]] = sources_raw if isinstance(sources_raw, list) else []
            
            # Extract tools_used with proper validation
            tools_used: List[str] = [
                str(source.get("source"))
                for source in sources
                if isinstance(source.get("source"), str) and source.get("status") == "success"
            ]
            
            # Validate status field
            status_raw = trends_data.get("status")
            status_str = status_raw if isinstance(status_raw, str) else "success"
            
            # Build metadata with validated data
            trends_metadata: Metadata = {
                "status": status_str,
                "tools_used": tools_used,
                "data_source": ", ".join(tools_used) if tools_used else "aggregated"
            }
            
            log_agent_step("fetch_trends_node", {
                "count": len(trends),
                "status": "success"
            }, "complete")
            
            # Return new state (immutable pattern - no mutation)
            return {
                **state,
                "trends": trends,
                "trends_metadata": trends_metadata
            }
            
        except Exception as e:
            # Handle errors gracefully with structured error
            log_agent_step("fetch_trends_node", {
                "error": str(e),
                "status": "failed"
            }, "error")
            
            # Structured error for production-ready debugging
            error_info: Dict[str, Union[str, JSONValue]] = {
                "type": "fetch_trends_error",
                "message": str(e),
                "node": "fetch_trends"
            }
            
            # Build failed metadata properly (not using constructor)
            failed_metadata: Metadata = {
                "status": "failed"
            }
            
            # Return new state with error (immutable pattern)
            return {
                **state,
                "trends": [],
                "trends_metadata": failed_metadata,
                "error": error_info
            }
