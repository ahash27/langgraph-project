"""Tests for Google Trends tool"""

import pytest
from app.tools.google_trends_tool import GoogleTrendsTool
from app.tools.tool_registry import ToolRegistry


def test_google_trends_tool_initialization():
    """Test tool initialization"""
    tool = GoogleTrendsTool()
    assert tool.name == "google_trends"
    assert tool.pytrends is not None


def test_region_normalization():
    """Test region code normalization"""
    tool = GoogleTrendsTool()
    
    assert tool._normalize_region("india") == "india"
    assert tool._normalize_region("IN") == "india"
    assert tool._normalize_region("India") == "india"
    assert tool._normalize_region("us") == "united_states"
    assert tool._normalize_region("USA") == "united_states"
    assert tool._normalize_region("uk") == "united_kingdom"


def test_tool_registry_includes_google_trends():
    """Test that Google Trends is registered"""
    tools = ToolRegistry.list_tools()
    assert "google_trends" in tools
    
    tool = ToolRegistry.get_tool("google_trends")
    assert isinstance(tool, GoogleTrendsTool)


@pytest.mark.skip(reason="Requires network access and may hit rate limits")
def test_fetch_trending_searches():
    """Test fetching trending searches (integration test)"""
    tool = GoogleTrendsTool()
    trends = tool.fetch_trending_searches(region="india")
    
    assert isinstance(trends, list)
    assert len(trends) > 0
    assert all(isinstance(t, str) for t in trends)


@pytest.mark.skip(reason="Requires network access and may hit rate limits")
def test_execute_without_keyword():
    """Test execute without specific keyword"""
    tool = GoogleTrendsTool()
    result = tool.execute(region="india", include_related=False)
    
    assert "region" in result
    assert "trends" in result
    assert "count" in result
    assert isinstance(result["trends"], list)


@pytest.mark.skip(reason="Requires network access and may hit rate limits")
def test_execute_with_keyword():
    """Test execute with specific keyword"""
    tool = GoogleTrendsTool()
    result = tool.execute(keyword="python", region="us", include_related=True)
    
    assert "region" in result
    assert "keyword" in result
    assert result["keyword"] == "python"
    assert "related_queries" in result


def test_safe_execute_structure():
    """Test safe_execute method exists and has correct signature"""
    tool = GoogleTrendsTool()
    assert hasattr(tool, "safe_execute")
    assert callable(tool.safe_execute)
