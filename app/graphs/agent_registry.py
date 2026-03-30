"""Agent registry for managing available agents"""

from typing import Dict, Type
from app.agents.base_agent import BaseAgent
from app.agents.coordinator_agent import CoordinatorAgent
from app.agents.processor_agent import ProcessorAgent
from app.agents.validator_agent import ValidatorAgent


class AgentRegistry:
    """
    Registry for managing and accessing agents.
    
    Provides centralized access to all available agents in the system.
    """
    
    _agents: Dict[str, Type[BaseAgent]] = {
        "coordinator": CoordinatorAgent,
        "processor": ProcessorAgent,
        "validator": ValidatorAgent,
    }
    
    @classmethod
    def get_agent(cls, agent_name: str) -> BaseAgent:
        """
        Get an agent instance by name.
        
        Args:
            agent_name: Name of the agent to retrieve
            
        Returns:
            Agent instance
            
        Raises:
            ValueError: If agent not found
        """
        agent_class = cls._agents.get(agent_name)
        if not agent_class:
            raise ValueError(f"Agent '{agent_name}' not found in registry")
        return agent_class()
    
    @classmethod
    def list_agents(cls) -> list:
        """Get list of all available agent names"""
        return list(cls._agents.keys())
    
    @classmethod
    def register_agent(cls, name: str, agent_class: Type[BaseAgent]):
        """Register a new agent"""
        cls._agents[name] = agent_class
