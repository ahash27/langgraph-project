"""Tests for sample graph"""

import pytest
from app.graphs.sample_graph import build_graph
from app.nodes.sample_node import hello_node

def test_hello_node():
    """Test hello node processing"""
    state = {"input": "Test"}
    result = hello_node(state)
    
    assert "message" in result
    assert "Test processed by LangGraph" in result["message"]

def test_build_graph():
    """Test graph compilation"""
    graph = build_graph()
    assert graph is not None

def test_graph_execution():
    """Test full graph execution"""
    graph = build_graph()
    result = graph.invoke({"input": "Hello"})
    
    assert "message" in result
    assert "Hello processed by LangGraph" in result["message"]
