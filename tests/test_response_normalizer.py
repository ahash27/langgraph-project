"""Tests for response normalizer"""

import pytest
from app.tools.response_normalizer import (
    normalize_tool_response,
    validate_normalized_response,
    compute_trend_score
)


def test_normalize_complete_response():
    """Test normalizing a complete response"""
    raw = {
        "source": "test_source",
        "status": "success",
        "trends": [
            {"topic": "AI", "rank": 1, "score": None}
        ],
        "count": 1
    }
    
    normalized = normalize_tool_response(raw, "test_source")
    
    assert normalized["source"] == "test_source"
    assert normalized["status"] == "success"
    assert len(normalized["trends"]) == 1
    assert normalized["count"] == 1


def test_normalize_missing_fields():
    """Test normalizing response with missing fields"""
    raw = {
        "trends": [
            {"topic": "Python"}
        ]
    }
    
    normalized = normalize_tool_response(raw, "fallback_source")
    
    # Should use fallback source name
    assert normalized["source"] == "fallback_source"
    # Should default to success
    assert normalized["status"] == "success"
    # Should have trends
    assert len(normalized["trends"]) == 1
    # Should compute count
    assert normalized["count"] == 1


def test_normalize_string_trends():
    """Test normalizing trends that are strings"""
    raw = {
        "trends": ["AI", "Python", "JavaScript"]
    }
    
    normalized = normalize_tool_response(raw, "test_source")
    
    assert len(normalized["trends"]) == 3
    assert all(isinstance(t, dict) for t in normalized["trends"])
    assert normalized["trends"][0]["topic"] == "AI"


def test_normalize_with_title_field():
    """Test normalizing trends with 'title' instead of 'topic'"""
    raw = {
        "trends": [
            {"title": "AI Technology", "rank": 1}
        ]
    }
    
    normalized = normalize_tool_response(raw, "test_source")
    
    assert normalized["trends"][0]["topic"] == "AI Technology"


def test_validate_normalized_response():
    """Test validation of normalized response"""
    valid = {
        "source": "test",
        "status": "success",
        "trends": [{"topic": "AI"}],
        "count": 1
    }
    
    assert validate_normalized_response(valid) is True


def test_validate_invalid_response():
    """Test validation fails for invalid response"""
    invalid = {
        "source": "test",
        # Missing status, trends, count
    }
    
    assert validate_normalized_response(invalid) is False


def test_compute_trend_score():
    """Test score computation"""
    trend = {"topic": "AI"}
    
    # Single source, rank 1
    score1 = compute_trend_score(trend, source_count=1, rank_sum=1)
    
    # Two sources, rank 2
    score2 = compute_trend_score(trend, source_count=2, rank_sum=2)
    
    # More sources should have higher score
    assert score2 > score1


def test_normalize_preserves_raw():
    """Test that normalization preserves raw response"""
    raw = {"trends": [{"topic": "AI"}]}
    
    normalized = normalize_tool_response(raw, "test")
    
    assert "raw_response" in normalized
    assert normalized["raw_response"] == raw
