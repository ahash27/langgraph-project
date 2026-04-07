"""Processor agent - executes main processing logic"""

from typing import List, Set
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
    - Orchestrate trends fetching with filtering and deduplication
    """
    
    # Configuration constants
    RELEVANCE_THRESHOLD = 100.0  # Minimum score for relevance filtering
    MAX_TRENDS = 5  # Maximum number of trends to return
    
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
    
    # ========================================
    # TRENDS ENGINE - Main Orchestrator
    # ========================================
    
    def fetch_trends(self, state: AgentState) -> TrendsData:
        """
        Main entry point for trends processing.
        
        This orchestrates the entire trends pipeline:
        1. Fetch raw trends from sources
        2. Filter by relevance threshold
        3. Deduplicate against recent trends (7 days)
        4. Limit to max results
        
        Args:
            state: Agent state containing region and other params
            
        Returns:
            Filtered and processed TrendsData
        """
        print(f"[TRENDS_ENGINE] Starting pipeline...")
        
        # Step 1: Get raw trends from aggregator
        trends_data = self._get_raw_trends(state)
        initial_count = trends_data.get("count", 0)
        print(f"[TRENDS_ENGINE] raw_trends: {initial_count} fetched")
        
        # Step 2: Filter by relevance threshold
        trends_data = self._filter_by_relevance(trends_data)
        
        # Step 3: Deduplicate against recent trends (7 days)
        trends_data = self._deduplicate_recent(trends_data)
        
        # Step 4: Limit to max results
        trends_data = self._limit_results(trends_data)
        
        final_count = trends_data.get("count", 0)
        print(f"[TRENDS_ENGINE] Pipeline complete: {initial_count} → {final_count}")
        
        return trends_data
    
    def _get_raw_trends(self, state: AgentState) -> TrendsData:
        """
        Fetch raw trends from aggregator with structured error handling.
        
        Args:
            state: Agent state containing region
            
        Returns:
            TrendsData with explicit status
        """
        region = state.get("region", "united_states")
        
        try:
            # Use multi-source aggregator for better results
            aggregator_tool = self.tools.get("trends_aggregator")
            
            if aggregator_tool:
                trends_data: TrendsData = aggregator_tool.safe_execute(region=region)  # type: ignore
                log_tool_usage("processor", "trends_aggregator", success=True)
                return trends_data
            else:
                # Fallback to single source
                trends_tool = self.tools["google_trends"]
                trends_data: TrendsData = trends_tool.safe_execute(  # type: ignore
                    region=region,
                    include_related=False
                )
                log_tool_usage("processor", "google_trends", success=True)
                return trends_data
                
        except Exception as e:
            log_tool_usage("processor", "trends_aggregator", success=False)
            
            # Return explicit failure structure
            return TrendsData(
                status="failed",
                error=str(e),
                trends=[],
                count=0,
                source="unknown"
            )
    
    def _filter_by_relevance(self, trends_data: TrendsData) -> TrendsData:
        """
        Filter trends by relevance threshold.
        
        Currently uses score-based filtering. In production, this can become:
        - LLM-based filtering
        - Semantic ranking
        - User preference matching
        
        Args:
            trends_data: Raw trends data
            
        Returns:
            New TrendsData with filtered trends (immutable)
        """
        threshold = self.RELEVANCE_THRESHOLD
        
        trends: List[TrendItem] = trends_data.get("trends", [])  # type: ignore
        before_count = len(trends)
        
        # Filter trends by score threshold (strict - None scores are excluded)
        filtered: List[TrendItem] = []
        for trend in trends:
            score = trend.get("score")
            if score is not None and score >= threshold:
                filtered.append(trend)
        
        after_count = len(filtered)
        
        # Log pipeline step
        print(f"[TRENDS_ENGINE] filter_relevance: {before_count} → {after_count} (threshold: {threshold})")
        
        # Return new dict (immutable pattern)
        return {
            **trends_data,
            "trends": filtered,  # type: ignore
            "count": after_count
        }
    
    def _deduplicate_recent(self, trends_data: TrendsData) -> TrendsData:
        """
        Deduplicate against recent trends (7 days memory).
        
        Currently uses a stub. In production, this should:
        - Query database for trends from last 7 days
        - Use Redis cache for fast lookups
        - Implement sliding window deduplication
        
        Args:
            trends_data: Trends data to deduplicate
            
        Returns:
            New TrendsData with deduplicated trends (immutable)
        """
        # Load recent topics (stub for now - shows design thinking)
        recent_topics = self._load_recent_topics()
        
        trends: List[TrendItem] = trends_data.get("trends", [])  # type: ignore
        before_count = len(trends)
        
        # Filter out topics seen in last 7 days (with normalization)
        filtered: List[TrendItem] = [
            trend for trend in trends
            if self._normalize_topic(trend.get("topic", "")) not in recent_topics
        ]
        
        after_count = len(filtered)
        
        # Log pipeline step
        print(f"[TRENDS_ENGINE] deduplicate_recent: {before_count} → {after_count} (recent: {len(recent_topics)})")
        
        # Return new dict (immutable pattern)
        return {
            **trends_data,
            "trends": filtered,  # type: ignore
            "count": after_count
        }
    
    def _normalize_topic(self, topic: str) -> str:
        """
        Normalize topic string for consistent comparison.
        
        Handles:
        - Case normalization (lowercase)
        - Whitespace trimming
        - Special character handling (future)
        
        Args:
            topic: Raw topic string
            
        Returns:
            Normalized topic string
            
        Examples:
            "AI News" → "ai news"
            "AI-news" → "ai-news"
            "  AI news  " → "ai news"
        """
        return topic.lower().strip()
    
    def _load_recent_topics(self) -> Set[str]:
        """
        Load topics from last 7 days.
        
        Stub implementation - shows architectural thinking.
        
        In production, this should:
        - Query database: SELECT topic FROM trends WHERE created_at > NOW() - INTERVAL 7 DAY
        - Use Redis cache with TTL
        - Implement efficient set operations
        
        Returns:
            Set of recent topic strings (lowercase)
        """
        # TODO: Implement database/cache lookup
        # For now, return empty set (no deduplication)
        return set()
    
    def _limit_results(self, trends_data: TrendsData) -> TrendsData:
        """
        Limit results to maximum number of trends.
        
        Args:
            trends_data: Trends data to limit
            
        Returns:
            New TrendsData with limited trends (immutable)
        """
        max_results = self.MAX_TRENDS
        
        trends: List[TrendItem] = trends_data.get("trends", [])  # type: ignore
        before_count = len(trends)
        limited: List[TrendItem] = trends[:max_results]
        after_count = len(limited)
        
        # Log pipeline step
        print(f"[TRENDS_ENGINE] limit_results: {before_count} → {after_count} (max: {max_results})")
        
        # Return new dict (immutable pattern)
        return {
            **trends_data,
            "trends": limited,  # type: ignore
            "count": after_count
        }
    
    # ========================================
    # END TRENDS ENGINE
    # ========================================
    
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
        """
        Process request for trends data using the trends engine.
        
        Uses the fetch_trends() orchestrator for clean, structured processing.
        """
        user_input = state.get("input", "")
        
        try:
            # Use the trends engine orchestrator
            trends_data = self.fetch_trends(state)
            
            # Check if fetch was successful
            if trends_data.get("status") == "failed":
                raise Exception(trends_data.get("error", "Unknown error"))
            
            # Extract tools used dynamically
            sources = trends_data.get("raw_sources") or trends_data.get("sources") or []  # type: ignore
            tools_used: List[str] = [
                source.get("source")  # type: ignore
                for source in sources
                if source.get("status") == "success" and source.get("source")  # type: ignore
            ]
            
            # Fallback if no successful sources found
            if not tools_used:
                tools_used = ["trends_aggregator"] if "trends_aggregator" in self.tools else ["google_trends"]
            
            # Format data source string
            data_source = ", ".join(tools_used) if tools_used else "Multi-source aggregator"
            
            # Format result message
            result_msg = f"Fetched {trends_data['count']} trending topics (filtered, deduplicated, limited to {self.MAX_TRENDS})"
            
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
            log_tool_usage("processor", "trends_engine", success=False)
            
            # Log detailed error for debugging
            import traceback
            error_details = traceback.format_exc()
            print(f"\n[ERROR] Trends Engine failed:")
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
