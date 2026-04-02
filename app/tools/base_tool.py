"""Base tool class for all tools"""

from abc import ABC, abstractmethod
from app.graphs.state_schema import JSONValue


class BaseTool(ABC):
    """
    Abstract base class for all tools.
    
    Tools are utilities that agents can use to perform specific actions.
    """
    
    def __init__(self, name: str, description: str = ""):
        self.name = name
        self.description = description
    
    @abstractmethod
    def execute(self, **kwargs) -> JSONValue:
        """
        Execute the tool's functionality.
        
        Args:
            **kwargs: Tool-specific parameters
            
        Returns:
            Tool execution result
        """
        pass
    
    def __call__(self, **kwargs) -> JSONValue:
        """Allow tool to be called as a function"""
        return self.execute(**kwargs)
