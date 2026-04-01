"""Tests for multi-agent system"""

import pytest
from app.agents.coordinator_agent import CoordinatorAgent
from app.agents.processor_agent import ProcessorAgent
from app.agents.validator_agent import ValidatorAgent
from app.graphs.agent_registry import AgentRegistry
from app.graphs.state_schema import SCHEMA_VERSION


def test_coordinator_agent():
    """Test coordinator agent execution"""
    agent = CoordinatorAgent()
    state = {"input": "Test task"}
    result = agent.execute(state)
    
    assert "plan" in result
    assert "next_agent" in result
    assert result["coordinator_status"] == "completed"
    assert result["schema_version"] == SCHEMA_VERSION
    assert all("name" in step for step in result["plan"]["steps"])


def test_processor_agent():
    """Test processor agent execution"""
    agent = ProcessorAgent()
    state = {
        "input": "Test input",
        "plan": {"task": "Test task", "steps": []}
    }
    result = agent.execute(state)
    
    assert "processed_output" in result
    assert result["processor_status"] == "completed"


def test_validator_agent():
    """Test validator agent execution"""
    agent = ValidatorAgent()
    state = {
        "processed_output": {"result": "Test result"}
    }
    result = agent.execute(state)
    
    assert "validation_result" in result
    assert "final_output" in result
    assert result["validator_status"] == "completed"


def test_validator_replaces_previous_issues():
    """Validator should report current issues, not accumulate stale ones."""
    agent = ValidatorAgent()
    state = {
        "processed_output": {
            "result": "Fresh result",
            "metadata": {"status": "success"},
        },
        "processor_confidence": 1.0,
        "issues": ["old issue"],
    }

    result = agent.execute(state)

    assert result["issues"] == []


def test_agents_do_not_mutate_input_history():
    """Agents should return updated history without mutating input state."""
    agent = CoordinatorAgent()
    state = {"input": "Test task", "execution_history": ["existing"]}

    result = agent.execute(state)

    assert state["execution_history"] == ["existing"]
    assert result["execution_history"] == ["existing", "coordinator"]


def test_agent_registry():
    """Test agent registry functionality"""
    agents = AgentRegistry.list_agents()
    
    assert "coordinator" in agents
    assert "processor" in agents
    assert "validator" in agents
    
    coordinator = AgentRegistry.get_agent("coordinator")
    assert isinstance(coordinator, CoordinatorAgent)
