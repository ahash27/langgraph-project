"""Base tool class for all tools"""

from typing import Dict, Any, Optional
from abc import ABC, abstractmethod


class BaseTool(ABC):
    """
    Abstract base class for all tools.
    
    Tools are utilities that agents can use to perform specific actions.
    """
    
    def __init__(self, name: str, description: str = ""):
        self.name = name
        self.description = description
    
    @abstractmethod
    def execute(self, **kwargs) -> Any:
        """
        Execute the tool's functionality.
        
        Args:
            **kwargs: Tool-specific parameters
            
        Returns:
            Tool execution result
        """
        pass
    
    def __call__(self, **kwargs) -> Any:
        """Allow tool to be called as a function"""
        return self.execute(**kwargs)
