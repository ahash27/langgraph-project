"""Fetch trends node - dedicated LangGraph node for trends pipeline"""

from typing import List
from app.agents.processor_agent import ProcessorAgent
from app.graphs.state_schema import AgentState, TrendItem, Metadata
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
    - Write top trends to state
    
    Architecture:
    - Reuses ProcessorAgent.fetch_trends() pipeline
    - Writes results directly to state["trends"]
    - Provides clean separation between orchestration and execution
    """
    
    def __init__(self):
        """Initialize with processor agent for pipeline reuse"""
        self.processor = ProcessorAgent()
    
    def __call__(self, state: AgentState) -> AgentState:
        """
        Execute trends fetching pipeline.
        
        Args:
            state: Agent state containing region and other params
            
        Returns:
            Updated state with trends and metadata
        """
        log_agent_step("fetch_trends_node", state, "start")
        
        try:
            # Use existing pipeline from ProcessorAgent
            trends_data = self.processor.fetch_trends(state)
            
            # Extract trends and metadata
            trends: List[TrendItem] = trends_data.get("trends", [])  # type: ignore
            
            # Write top trends to state
            state["trends"] = trends
            
            # Write metadata for observability
            sources = trends_data.get("raw_sources") or trends_data.get("sources") or []  # type: ignore
            tools_used: List[str] = [
                source.get("source")  # type: ignore
                for source in sources
                if source.get("status") == "success" and source.get("source")  # type: ignore
            ]
            
            trends_metadata: Metadata = {
                "status": trends_data.get("status", "success"),
                "tools_used": tools_used,
                "data_source": ", ".join(tools_used) if tools_used else "trends_aggregator"
            }
            
            state["trends_metadata"] = trends_metadata  # type: ignore
            
            log_agent_step("fetch_trends_node", {
                "count": len(trends),
                "status": "success"
            }, "complete")
            
            return state
            
        except Exception as e:
            # Handle errors gracefully
            log_agent_step("fetch_trends_node", {
                "error": str(e),
                "status": "failed"
            }, "error")
            
            # Write empty trends and error to state
            state["trends"] = []
            state["trends_metadata"] = Metadata(  # type: ignore
                status="failed"
            )
            state["error"] = str(e)  # type: ignore
            
            return state
