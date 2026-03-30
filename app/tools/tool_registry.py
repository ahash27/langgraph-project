"""Tool registry for managing available tools"""

from typing import Dict, Type
from app.tools.base_tool import BaseTool
from app.tools.data_transformer import DataTransformer
from app.tools.validator_tool import ValidatorTool


class ToolRegistry:
    """
    Registry for managing and accessing tools.
    
    Provides centralized access to all available tools in the system.
    """
    
    _tools: Dict[str, Type[BaseTool]] = {
        "data_transformer": DataTransformer,
        "validator_tool": ValidatorTool,
    }
    
    @classmethod
    def get_tool(cls, tool_name: str) -> BaseTool:
        """
        Get a tool instance by name.
        
        Args:
            tool_name: Name of the tool to retrieve
            
        Returns:
            Tool instance
            
        Raises:
            ValueError: If tool not found
        """
        tool_class = cls._tools.get(tool_name)
        if not tool_class:
            raise ValueError(f"Tool '{tool_name}' not found in registry")
        return tool_class()
    
    @classmethod
    def list_tools(cls) -> list:
        """Get list of all available tool names"""
        return list(cls._tools.keys())
    
    @classmethod
    def register_tool(cls, name: str, tool_class: Type[BaseTool]):
        """Register a new tool"""
        cls._tools[name] = tool_class
