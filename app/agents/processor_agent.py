"""Processor agent - executes main processing logic"""

from typing import List
from app.agents.base_agent import BaseAgent
from app.graphs.state_schema import (
    AgentPlan,
    AgentState,
    Metadata,
    ProcessedOutput,
    TrendsData,
)
from app.tools.tool_registry import ToolRegistry
from app.utils.logger import log_agent_step, log_tool_usage


class ProcessorAgent(BaseAgent):
    """
    Processor agent that executes main task logic.
    
    Responsibilities:
    - Execute core processing based on plan
    - Transform input data using tools
    - Generate intermediate results
    - Provide confidence scores
    - Integrate with external data sources (e.g., Google Trends)
    """
    
    def __init__(self):
        super().__init__(
            name="processor",
            description="Executes main processing logic based on coordinator's plan"
        )
        self.tools = {}
        self._load_tools()
    
    def _load_tools(self):
        """Load available tools from registry"""
        try:
            for tool_name in ToolRegistry.list_tools():
                self.tools[tool_name] = ToolRegistry.get_tool(tool_name)
        except Exception:
            pass  # Tools optional for basic operation
    
    def _detect_intent(self, user_input: str, plan: AgentPlan) -> str:
        """
        Detect user intent from input and plan.
        
        Args:
            user_input: User's input text
            plan: Execution plan from coordinator
            
        Returns:
            Intent string (e.g., 'trends', 'transform', 'generic')
            
        Note:
            This is a simple keyword-based approach. In production, consider:
            - Using LLM for intent classification
            - Training a dedicated intent classifier
            - Using embeddings for semantic matching
            - Maintaining intent history for context
        """
        input_lower = user_input.lower()
        
        # Check for trends-related keywords
        trends_keywords = ['trend', 'trending', 'popular', 'viral', 'google trends']
        if any(keyword in input_lower for keyword in trends_keywords):
            return 'trends'
        
        # Check plan for explicit intent
        if 'intent' in plan:
            return plan['intent']
        
        return 'generic'
    
    def execute(self, state: AgentState) -> AgentState:
        """
        Process the task according to plan with tool integration.
        
        Args:
            state: Must contain 'plan' from coordinator
            
        Returns:
            State with 'processed_output', confidence, and routing
        """
        log_agent_step("processor", state, "start")
        
        plan: AgentPlan = state.get("plan", {})  # type: ignore
        user_input: str = state.get("input", "")
        execution_history: List[str] = state.get("execution_history", [])
        
        # Detect intent
        intent = self._detect_intent(user_input, plan)
        
        # Handle trends intent
        if intent == "trends" and (
            "google_trends" in self.tools or "trends_aggregator" in self.tools
        ):
            return self._process_trends_request(state, plan, execution_history)
        
        # Default processing with data transformation
        return self._process_generic_request(state, plan, execution_history)
    
    def _process_trends_request(
        self, 
        state: AgentState, 
        plan: AgentPlan,
        execution_history: List[str]
    ) -> AgentState:
        """Process request for Google Trends data"""
        user_input = state.get("input", "")
        
        try:
            # Extract region from input or use default
            region = state.get("region", "united_states")  # Changed default
            
            # Use multi-source aggregator for better results
            aggregator_tool = self.tools.get("trends_aggregator")
            
            if aggregator_tool:
                # Use aggregator (combines Google Trends + DuckDuckGo)
                trends_data: TrendsData = aggregator_tool.safe_execute(region=region)  # type: ignore
                log_tool_usage("processor", "trends_aggregator", success=True)
                
                # Extract tools dynamically from aggregator response
                # Resilient to schema changes: try raw_sources, then sources, then empty list
                sources = trends_data.get("raw_sources") or trends_data.get("sources") or []  # type: ignore
                tools_used: List[str] = [
                    source.get("source")  # type: ignore
                    for source in sources
                    if source.get("status") == "success" and source.get("source")  # type: ignore
                ]
                
                # Fallback if no successful sources found
                if not tools_used:
                    tools_used = ["trends_aggregator"]
                
                # Format data source string
                data_source = ", ".join(tools_used) if tools_used else "Multi-source aggregator"
                
                # Format aggregated result
                result_msg = f"Fetched {trends_data['count']} trending topics from {trends_data['sources_successful']} sources"
            else:
                # Fallback to single source
                trends_tool = self.tools["google_trends"]
                trends_data: TrendsData = trends_tool.safe_execute(  # type: ignore
                    region=region,
                    include_related=False  # Faster, avoid rate limits
                )
                log_tool_usage("processor", "google_trends", success=True)
                tools_used: List[str] = ["google_trends"]
                data_source: str = "Google Trends"
                result_msg: str = f"Fetched {trends_data.get('count', 0)} trending topics"
            
            # Format output
            metadata: Metadata = {
                "status": "success",
                "tools_used": tools_used,
                "data_source": data_source
            }
            
            processed_output: ProcessedOutput = {
                "original_input": user_input,
                "intent": "trends",
                "result": result_msg,
                "trends_data": trends_data,
                "metadata": metadata
            }
            
            confidence = 0.95  # High confidence for successful API call
            
        except Exception as e:
            log_tool_usage("processor", "google_trends", success=False)
            
            # Log detailed error for debugging
            import traceback
            error_details = traceback.format_exc()
            print(f"\n[ERROR] Trends API failed:")
            print(f"  Error: {str(e)}")
            print(f"  Details: {error_details}\n")
            
            # Determine which tool failed
            failed_tool: str = "trends_aggregator" if "trends_aggregator" in self.tools else "google_trends"
            
            metadata: Metadata = {
                "status": "error",
                "tools_used": [failed_tool]
            }
            
            processed_output: ProcessedOutput = {
                "original_input": user_input,
                "intent": "trends",
                "result": f"Failed to fetch trends: {str(e)}",
                "error": str(e),
                "error_details": error_details,
                "metadata": metadata
            }
            
            confidence = 0.3  # Low confidence on error
        
        log_agent_step("processor", {"confidence": confidence, "intent": "trends"}, "complete")

        hist = [*execution_history, "processor"]

        return {
            **state,
            "processed_output": processed_output,
            "processor_confidence": confidence,
            "next_agent": "validator",
            "processor_status": "completed",
            "current_agent": "processor",
            "execution_history": hist,
        }

    def _process_generic_request(
        self,
        state: AgentState,
        plan: AgentPlan,
        execution_history: List[str],
    ) -> AgentState:
        """Process generic request with data transformation"""
        user_input = state.get("input", "")

        transformed_data = user_input
        tools_used: List[str] = []

        if "data_transformer" in plan.get("requires_tools", []):
            if "data_transformer" in self.tools:
                try:
                    transformed_data = self.tools["data_transformer"].execute(
                        user_input,
                        transform_type="normalize",
                    )
                    tools_used.append("data_transformer")
                    log_tool_usage("processor", "data_transformer", success=True)
                except Exception:
                    log_tool_usage("processor", "data_transformer", success=False)

        complexity: float = plan.get("complexity", 0.5)
        confidence: float = 1.0 - (complexity * 0.3)

        metadata: Metadata = {
            "steps_completed": len(plan.get("steps", [])),
            "status": "success",
            "tools_used": tools_used,
        }

        processed_output: ProcessedOutput = {
            "original_input": user_input,
            "transformed_input": transformed_data,
            "plan_executed": plan.get("task", ""),
            "result": f"Processed: {transformed_data}",
            "metadata": metadata,
        }

        log_agent_step("processor", {"confidence": confidence}, "complete")

        hist = [*execution_history, "processor"]

        return {
            **state,
            "processed_output": processed_output,
            "processor_confidence": confidence,
            "next_agent": "validator",
            "processor_status": "completed",
            "current_agent": "processor",
            "execution_history": hist,
        }
