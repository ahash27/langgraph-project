"""Validator agent - validates and quality checks output"""

from typing import List

from app.agents.base_agent import BaseAgent
from app.graphs.state_schema import AgentState, FinalOutput, ProcessedOutput, ValidationResult
from app.tools.tool_registry import ToolRegistry
from app.utils.logger import log_agent_step, log_tool_usage, log_routing_decision


class ValidatorAgent(BaseAgent):
    """
    Validator agent that checks quality and correctness.
    
    Responsibilities:
    - Validate processed output
    - Check quality criteria
    - Approve or request revision
    - Decide if retry needed
    """
    
    def __init__(self):
        super().__init__(
            name="validator",
            description="Validates output quality and correctness"
        )
        self.tools = {}
        self._load_tools()
    
    def _load_tools(self):
        """Load validation tools"""
        try:
            if "validator_tool" in ToolRegistry.list_tools():
                self.tools["validator_tool"] = ToolRegistry.get_tool("validator_tool")
        except Exception:
            pass
    
    def execute(self, state: AgentState) -> AgentState:
        """
        Validate the processed output with retry logic.
        
        Args:
            state: Must contain 'processed_output' from processor
            
        Returns:
            State with validation result and routing decision
        """
        log_agent_step("validator", state, "start")
        
        processed = state.get("processed_output", {})
        confidence = state.get("processor_confidence", 1.0)
        retry_count = state.get("retry_count", 0)
        max_retries = state.get("max_retries", 3)
        execution_history = [*state.get("execution_history", [])]
        
        # Run validation checks
        issues = self._validate_output(processed, confidence)
        is_valid = len(issues) == 0
        quality_score = self._calculate_quality_score(processed, confidence, issues)
        
        # Determine if retry needed
        needs_retry = not is_valid and retry_count < max_retries
        
        validation_result: ValidationResult = {
            "is_valid": is_valid,
            "quality_score": quality_score,
            "checks_passed": self._get_passed_checks(issues),
            "issues": issues,
            "needs_retry": needs_retry
        }
        
        # Decide next step
        if is_valid:
            next_agent = "end"
            status = "approved"
            workflow_status = "completed_success"
        elif needs_retry:
            next_agent = "processor"  # Loop back for retry
            status = "retry_requested"
            workflow_status = "retrying"
            log_routing_decision("validator", "processor", f"retry {retry_count + 1}/{max_retries}")
        else:
            next_agent = "end"
            status = "rejected"
            workflow_status = "completed_with_issues"
        
        final_output: FinalOutput = {
            "result": processed.get("result", ""),
            "validation": validation_result,
            "status": status,
            "retry_count": retry_count
        }
        
        log_agent_step("validator", {
            "is_valid": is_valid,
            "quality_score": quality_score,
            "issues": len(issues)
        }, "complete")
        
        return {
            **state,
            "validation_result": validation_result,
            "is_valid": is_valid,
            "validation_score": quality_score,
            "issues": issues,
            "final_output": final_output,
            "next_agent": next_agent,
            "validator_status": "completed",
            "retry_count": retry_count + 1 if needs_retry else retry_count,
            "current_agent": "validator",
            "workflow_status": workflow_status,
            "execution_history": [*execution_history, "validator"]
        }
    
    def _validate_output(self, processed: ProcessedOutput, confidence: float) -> List[str]:
        """Run validation checks and return issues"""
        issues = []
        
        # Check if result exists
        if not processed.get("result"):
            issues.append("Missing result field")
        
        # Check confidence threshold
        if confidence < 0.6:
            issues.append(f"Low confidence: {confidence:.2f}")
        
        # Check metadata
        metadata = processed.get("metadata", {})
        if metadata.get("status") != "success":
            issues.append("Processing status not successful")
        
        # Use validator tool if available
        if "validator_tool" in self.tools:
            try:
                tool_result = self.tools["validator_tool"].execute(
                    processed.get("result", ""),
                    checks=["not_empty", "format_check"]
                )
                log_tool_usage("validator", "validator_tool", tool_result["is_valid"])
                if not tool_result["is_valid"]:
                    issues.extend(tool_result["errors"])
            except Exception:
                log_tool_usage("validator", "validator_tool", False)
        
        return issues
    
    def _calculate_quality_score(
        self,
        processed: ProcessedOutput,
        confidence: float,
        issues: List[str]
    ) -> float:
        """Calculate overall quality score"""
        base_score = 1.0
        
        # Deduct for issues
        base_score -= len(issues) * 0.15
        
        # Factor in confidence
        base_score *= confidence
        
        return max(0.0, min(1.0, base_score))
    
    def _get_passed_checks(self, issues: List[str]) -> List[str]:
        """Get list of checks that passed"""
        all_checks = [
            "format_check",
            "completeness_check",
            "consistency_check",
            "confidence_check"
        ]
        
        # Simple heuristic - checks pass if no related issues
        passed = []
        for check in all_checks:
            if not any(check.split("_")[0] in issue.lower() for issue in issues):
                passed.append(check)
        
        return passed
