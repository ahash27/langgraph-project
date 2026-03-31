"""Response normalizer for ensuring consistent tool output format"""

from typing import Dict, Any, List


def normalize_tool_response(
    response: Dict[str, Any], 
    source_name: str
) -> Dict[str, Any]:
    """
    Normalize tool response to consistent format.
    
    This is a self-healing layer that ensures all tools return
    data in the expected format, regardless of their implementation.
    
    Args:
        response: Raw response from tool
        source_name: Name of the source tool
        
    Returns:
        Normalized response with guaranteed fields
        
    Example:
        >>> raw = {"trends": [...]}
        >>> normalized = normalize_tool_response(raw, "google_trends")
        >>> # Now guaranteed to have: source, status, trends, error, count
    """
    # Extract or default each field
    source = response.get("source", source_name)
    status = response.get("status", "success")
    trends = response.get("trends", [])
    error = response.get("error", None)
    count = response.get("count", len(trends))
    
    # Validate trends structure
    normalized_trends = []
    for trend in trends:
        if isinstance(trend, dict):
            # Ensure each trend has required fields
            normalized_trend = {
                "topic": trend.get("topic", trend.get("title", "")),
                "rank": trend.get("rank", 0),
                "score": trend.get("score", None),
                "source": source,
                "link": trend.get("link", None),
                "description": trend.get("description", trend.get("body", ""))
            }
            normalized_trends.append(normalized_trend)
        elif isinstance(trend, str):
            # Handle string trends (convert to dict)
            normalized_trends.append({
                "topic": trend,
                "rank": 0,
                "score": None,
                "source": source,
                "link": None,
                "description": ""
            })
    
    # Build normalized response
    normalized = {
        "source": source,
        "status": status,
        "trends": normalized_trends,
        "count": len(normalized_trends),
        "error": error,
        "raw_response": response  # Keep original for debugging
    }
    
    return normalized


def validate_normalized_response(response: Dict[str, Any]) -> bool:
    """
    Validate that a response has been properly normalized.
    
    Args:
        response: Response to validate
        
    Returns:
        True if valid, False otherwise
    """
    required_fields = ["source", "status", "trends", "count"]
    
    # Check required fields exist
    if not all(field in response for field in required_fields):
        return False
    
    # Check trends is a list
    if not isinstance(response["trends"], list):
        return False
    
    # Check each trend has required fields
    for trend in response["trends"]:
        if not isinstance(trend, dict):
            return False
        if "topic" not in trend:
            return False
    
    return True


def compute_trend_score(
    trend: Dict[str, Any],
    source_count: int,
    rank_sum: int
) -> float:
    """
    Compute aggregated score for a trend.
    
    This is a COMPUTED score, not from any API.
    
    Scoring algorithm:
    - More sources = higher score (100 points per source)
    - Lower rank = higher score (1000 / rank_sum)
    
    Args:
        trend: Trend data
        source_count: Number of sources that have this trend
        rank_sum: Sum of ranks across sources
        
    Returns:
        Computed score (higher is better)
        
    Note:
        This is NOT an API-provided score. It's computed based on:
        1. Cross-source frequency (appears in multiple sources)
        2. Ranking position (lower rank = more popular)
    """
    # Source score: 100 points per source
    source_score = source_count * 100
    
    # Rank score: inverse of rank sum (lower rank = higher score)
    rank_score = 1000 / (rank_sum + 1) if rank_sum > 0 else 0
    
    # Total score
    total_score = source_score + rank_score
    
    return round(total_score, 1)
