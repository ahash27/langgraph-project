"""Base agent class for all agents"""

from abc import ABC, abstractmethod
from app.graphs.state_schema import AgentState

from app.graphs.state_schema import AgentState


class BaseAgent(ABC):
    """
    Abstract base class for all agents in the system.
    
    Each agent should implement the execute method to define its behavior.
    """
    
    def __init__(self, name: str, description: str = ""):
        self.name = name
        self.description = description
    
    @abstractmethod
    def execute(self, state: AgentState) -> AgentState:
        """
        Execute the agent's logic.
        
        Args:
            state: Current state containing all context
            
        Returns:
            Updated state with agent's output
        """
        pass
    
    def __call__(self, state: AgentState) -> AgentState:
        """Allow agent to be called as a function"""
        return self.execute(state)
