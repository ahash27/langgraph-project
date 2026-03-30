"""Processor agent - executes main processing logic"""

from typing import Dict, Any, List
from app.agents.base_agent import BaseAgent
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
    
    def execute(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """
        Process the task according to plan with tool integration.
        
        Args:
            state: Must contain 'plan' from coordinator
            
        Returns:
            State with 'processed_output', confidence, and routing
        """
        log_agent_step("processor", state, "start")
        
        plan = state.get("plan", {})
        user_input = state.get("input", "")
        execution_history = state.get("execution_history", [])
        
        # Use tools if specified in plan
        transformed_data = user_input
        tools_used = []
        
        if "data_transformer" in plan.get("requires_tools", []):
            if "data_transformer" in self.tools:
                try:
                    transformed_data = self.tools["data_transformer"].execute(
                        user_input, 
                        transform_type="normalize"
                    )
                    tools_used.append("data_transformer")
                    log_tool_usage("processor", "data_transformer", success=True)
                except Exception as e:
                    log_tool_usage("processor", "data_transformer", success=False)
        
        # Calculate confidence based on complexity
        complexity = plan.get("complexity", 0.5)
        confidence = 1.0 - (complexity * 0.3)  # Higher complexity = lower confidence
        
        # Generic processing logic
        processed_output = {
            "original_input": user_input,
            "transformed_input": transformed_data,
            "plan_executed": plan.get("task", ""),
            "result": f"Processed: {transformed_data}",
            "metadata": {
                "steps_completed": len(plan.get("steps", [])),
                "status": "success",
                "tools_used": tools_used
            }
        }
        
        log_agent_step("processor", {"confidence": confidence}, "complete")
        
        # Update execution history
        execution_history.append("processor")
        
        return {
            **state,
            "processed_output": processed_output,
            "processor_confidence": confidence,
            "next_agent": "validator",
            "processor_status": "completed",
            "current_agent": "processor",
            "execution_history": execution_history
        }
