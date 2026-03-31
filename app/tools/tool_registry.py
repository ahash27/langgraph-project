"""Tool registry for managing available tools"""

from typing import Dict, Type
from app.tools.base_tool import BaseTool
from app.tools.data_transformer import DataTransformer
from app.tools.validator_tool import ValidatorTool
from app.tools.google_trends_tool import GoogleTrendsTool
from app.tools.duckduckgo_trends_tool import DuckDuckGoTrendsTool
from app.tools.trends_aggregator import TrendsAggregatorTool


class ToolRegistry:
    """
    Registry for managing and accessing tools.
    
    Provides centralized access to all available tools in the system.
    """
    
    _tools: Dict[str, Type[BaseTool]] = {
        "data_transformer": DataTransformer,
        "validator_tool": ValidatorTool,
        "google_trends": GoogleTrendsTool,
        "duckduckgo_trends": DuckDuckGoTrendsTool,
    }
    
    # Lazy-initialized aggregator
    _aggregator = None
    
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
        # Handle aggregator specially (needs other tools)
        if tool_name == "trends_aggregator":
            if cls._aggregator is None:
                # Initialize aggregator with trends tools
                trends_tools = {
                    "google_trends": cls.get_tool("google_trends"),
                    "duckduckgo_trends": cls.get_tool("duckduckgo_trends")
                }
                cls._aggregator = TrendsAggregatorTool(trends_tools)
            return cls._aggregator
        
        tool_class = cls._tools.get(tool_name)
        if not tool_class:
            raise ValueError(f"Tool '{tool_name}' not found in registry")
        return tool_class()
    
    @classmethod
    def list_tools(cls) -> list:
        """Get list of all available tool names"""
        return list(cls._tools.keys()) + ["trends_aggregator"]
    
    @classmethod
    def register_tool(cls, name: str, tool_class: Type[BaseTool]):
        """Register a new tool"""
        cls._tools[name] = tool_class
