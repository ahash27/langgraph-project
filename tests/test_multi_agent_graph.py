"""Tests for multi-agent graph"""

import pytest
from app.graphs.multi_agent_graph import build_multi_agent_graph
from app.graphs.state_schema import SCHEMA_VERSION


def test_build_multi_agent_graph():
    """Test multi-agent graph compilation"""
    graph = build_multi_agent_graph()
    assert graph is not None


def test_multi_agent_execution():
    """Test full multi-agent workflow execution"""
    graph = build_multi_agent_graph()
    
    result = graph.invoke({
        "input": "Test multi-agent workflow"
    })
    
    # Check all agents executed
    assert result["coordinator_status"] == "completed"
    assert result["processor_status"] == "completed"
    assert result["validator_status"] == "completed"
    
    # Check outputs exist
    assert "plan" in result
    assert "processed_output" in result
    assert "final_output" in result
    assert "validation_result" in result
    assert result["schema_version"] == SCHEMA_VERSION
    assert result["execution_history"] == [
        "coordinator",
        "processor",
        "generate_posts",
        "validator",
    ]
    assert result.get("generate_posts_status") == "completed"
    assert "thought_leadership" in (result.get("generated_posts") or {})
