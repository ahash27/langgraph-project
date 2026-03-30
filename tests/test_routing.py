"""Tests for dynamic routing logic"""

import pytest
from app.graphs.multi_agent_graph import (
    route_after_validator,
    route_after_coordinator,
    build_multi_agent_graph
)


def test_route_after_validator_success():
    """Test routing when validation passes"""
    state = {
        "is_valid": True,
        "retry_count": 0,
        "max_retries": 3
    }
    
    result = route_after_validator(state)
    assert result == "end"


def test_route_after_validator_retry():
    """Test routing when validation fails with retries available"""
    state = {
        "is_valid": False,
        "retry_count": 1,
        "max_retries": 3
    }
    
    result = route_after_validator(state)
    assert result == "processor"


def test_route_after_validator_max_retries():
    """Test routing when max retries reached"""
    state = {
        "is_valid": False,
        "retry_count": 3,
        "max_retries": 3
    }
    
    result = route_after_validator(state)
    assert result == "end"


def test_route_after_coordinator():
    """Test coordinator routing logic"""
    state = {
        "plan": {
            "complexity": 0.7
        }
    }
    
    result = route_after_coordinator(state)
    assert result == "processor"


def test_retry_loop_integration():
    """Test full retry loop in graph"""
    graph = build_multi_agent_graph()
    
    # This should trigger a retry scenario
    result = graph.invoke({
        "input": "Test task that might need retry"
    })
    
    # Check workflow executed
    assert "coordinator_status" in result
    assert "processor_status" in result
    assert "validator_status" in result
    assert "final_output" in result
