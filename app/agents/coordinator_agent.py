"""Coordinator agent - orchestrates workflow and delegates tasks"""

from app.agents.base_agent import BaseAgent
from app.graphs.state_schema import AgentPlan, AgentState, PlanStep, SCHEMA_VERSION
from app.utils.logger import log_agent_step, log_routing_decision


class CoordinatorAgent(BaseAgent):
    """
    Coordinator agent that analyzes input and creates execution plan.
    
    Responsibilities:
    - Understand user request
    - Break down into subtasks
    - Determine which agents to invoke
    - Create execution plan
    - DECIDE next agent (true autonomy)
    """
    
    def __init__(self):
        super().__init__(
            name="coordinator",
            description="Orchestrates workflow and delegates tasks to specialized agents"
        )
    
    def execute(self, state: AgentState) -> AgentState:
        """
        Analyze input and create execution plan with autonomous routing.
        
        Args:
            state: Must contain 'input' key with user request
            
        Returns:
            State with 'plan', 'next_agent' decided by coordinator
        """
        log_agent_step("coordinator", state, "start")
        
        user_input = state.get("input", "")
        retry_count = state.get("retry_count", 0)
        execution_history = [*state.get("execution_history", []), "coordinator"]
        
        # Analyze complexity and determine strategy
        complexity = self._analyze_complexity(user_input)
        
        # COORDINATOR DECIDES NEXT AGENT (true autonomy)
        next_agent = self._decide_next_agent(complexity, retry_count)
        
        # Generic planning logic with routing
        plan_steps: list[PlanStep] = [
            {"name": "Analyze request", "status": "pending"},
            {"name": "Execute processing", "status": "pending"},
            {"name": "Validate output", "status": "pending"},
        ]
        plan: AgentPlan = {
            "task": user_input,
            "complexity": complexity,
            "steps": plan_steps,
            "priority": "normal",
            "requires_tools": ["data_transformer"] if complexity > 0.5 else [],
        }
        
        log_routing_decision("coordinator", next_agent, f"complexity={complexity:.2f}")
        log_agent_step("coordinator", {"plan": plan}, "complete")
        
        return {
            **state,
            "schema_version": SCHEMA_VERSION,
            "plan": plan,
            "next_agent": next_agent,
            "coordinator_status": "completed",
            "retry_count": retry_count,
            "max_retries": 3,
            "current_agent": "coordinator",
            "execution_history": execution_history
        }
    
    def _analyze_complexity(self, input_text: str) -> float:
        """Analyze task complexity (0.0 to 1.0)"""
        # Simple heuristic - can be enhanced with LLM
        word_count = len(input_text.split())
        if word_count < 5:
            return 0.3
        elif word_count < 15:
            return 0.6
        else:
            return 0.9
    
    def _decide_next_agent(self, complexity: float, retry_count: int) -> str:
        """
        Coordinator decides which agent to route to.
        
        This is TRUE autonomy - coordinator controls the graph flow.
        """
        # For very simple tasks, could skip processor (future enhancement)
        if complexity < 0.2:
            return "processor"  # Could be "validator" for simple tasks
        
        # Normal flow
        return "processor"
