"""Tests for tools"""

import pytest
from app.tools.data_transformer import DataTransformer
from app.tools.validator_tool import ValidatorTool
from app.tools.tool_registry import ToolRegistry


def test_data_transformer():
    """Test data transformer tool"""
    tool = DataTransformer()
    
    # Test normalize
    result = tool.execute("  TEST  ", transform_type="normalize")
    assert result == "test"
    
    # Test format
    result = tool.execute(123, transform_type="format")
    assert result == "123"


def test_validator_tool():
    """Test validator tool"""
    tool = ValidatorTool()
    
    # Test with valid data
    result = tool.execute("test data", checks=["not_empty", "format_check"])
    assert result["is_valid"] is True
    assert len(result["errors"]) == 0
    
    # Test with empty data
    result = tool.execute("", checks=["not_empty"])
    assert result["is_valid"] is False


def test_tool_registry():
    """Test tool registry functionality"""
    tools = ToolRegistry.list_tools()
    
    assert "data_transformer" in tools
    assert "validator_tool" in tools
    
    transformer = ToolRegistry.get_tool("data_transformer")
    assert isinstance(transformer, DataTransformer)
