"""Validation tool for checking data quality"""

from typing import Dict, List
from app.tools.base_tool import BaseTool
from app.graphs.state_schema import JSONValue


class ValidatorTool(BaseTool):
    """
    Tool for validating data quality and correctness.
    
    Provides various validation checks that agents can use.
    """
    
    def __init__(self):
        super().__init__(
            name="validator_tool",
            description="Validates data quality, format, and correctness"
        )
    
    def execute(self, data: JSONValue, checks: List[str] = None) -> Dict[str, JSONValue]:
        """
        Run validation checks on data.
        
        Args:
            data: Data to validate
            checks: List of check types to run
            
        Returns:
            Validation result dictionary
        """
        if checks is None:
            checks = ["not_empty", "type_check"]
        
        results = {
            "is_valid": True,
            "checks": {},
            "errors": []
        }
        
        for check in checks:
            check_result = self._run_check(data, check)
            results["checks"][check] = check_result
            if not check_result:
                results["is_valid"] = False
                results["errors"].append(f"Failed: {check}")
        
        return results
    
    def _run_check(self, data: JSONValue, check_type: str) -> bool:
        """Run specific validation check"""
        if check_type == "not_empty":
            return data is not None and data != ""
        elif check_type == "type_check":
            return True  # Generic type check
        elif check_type == "format_check":
            return isinstance(data, (str, dict, list))
        return True
