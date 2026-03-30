"""Base agent class for all agents"""

from typing import Dict, Any, Optional
from abc import ABC, abstractmethod


class BaseAgent(ABC):
    """
    Abstract base class for all agents in the system.
    
    Each agent should implement the execute method to define its behavior.
    """
    
    def __init__(self, name: str, description: str = ""):
        self.name = name
        self.description = description
    
    @abstractmethod
    def execute(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute the agent's logic.
        
        Args:
            state: Current state dictionary containing all context
            
        Returns:
            Updated state dictionary with agent's output
        """
        pass
    
    def __call__(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """Allow agent to be called as a function"""
        return self.execute(state)
