# Google Trends Tool Integration

## Overview

The Google Trends tool provides real-time access to trending topics and related queries from Google Trends API via the `pytrends` library.

## Features

✅ **Trending Searches** - Fetch daily trending topics by region  
✅ **Related Queries** - Get related search queries for any topic  
✅ **Region Support** - Multiple regions (India, US, UK, etc.)  
✅ **Rate Limiting** - Built-in protection against API rate limits  
✅ **Retry Logic** - Exponential backoff on failures  
✅ **Agent Integration** - Automatically used when "trends" detected in input  

## Installation

```bash
pip install pytrends
```

## Usage

### Standalone Usage

```python
from app.tools.google_trends_tool import GoogleTrendsTool

tool = GoogleTrendsTool()

# Fetch trending topics
result = tool.safe_execute(region="india", include_related=True)

print(f"Region: {result['region']}")
print(f"Found {result['count']} trends")

for trend in result['trends']:
    print(f"- {trend['topic']}")
    if trend['related_queries']:
        print(f"  Related: {', '.join(trend['related_queries'][:3])}")
```

### Via Tool Registry

```python
from app.tools.tool_registry import ToolRegistry

tool = ToolRegistry.get_tool("google_trends")
result = tool.safe_execute(region="us")
```

### Multi-Agent Integration

The processor agent automatically detects "trends" intent:

```python
from app.graphs.multi_agent_graph import build_multi_agent_graph

graph = build_multi_agent_graph()

# These inputs trigger Google Trends tool
result = graph.invoke({"input": "Show me trending topics"})
result = graph.invoke({"input": "What's popular on Google?"})
result = graph.invoke({"input": "Get viral trends"})
```

## API Reference

### GoogleTrendsTool.execute()

```python
def execute(
    keyword: Optional[str] = None,
    region: str = "india",
    include_related: bool = True
) -> Dict[str, Any]
```

**Parameters:**
- `keyword` (optional): Specific keyword to analyze
- `region`: Region code (default: "india")
- `include_related`: Fetch related queries (default: True)

**Returns:**
```python
{
    "region": "india",
    "count": 10,
    "trends": [
        {
            "topic": "Example Topic",
            "rank": 1,  # Position in trending list (1-10)
            "score": None,  # Google Trends doesn't provide scores
            "related_queries": ["query1", "query2"],
            "related_queries_error": None  # Error info if fetch failed
        }
    ]
}
```

**Note on Scores**: Google Trends API does not provide absolute popularity scores. Use `rank` (1-10) as a proxy for relative popularity.

### GoogleTrendsTool.safe_execute()

Same as `execute()` but with retry logic:

```python
def safe_execute(
    max_retries: int = 3,
    **kwargs
) -> Dict[str, Any]
```

**Features:**
- Exponential backoff (2^attempt seconds)
- Automatic retry on failure
- Raises exception after max retries

## Supported Regions

The tool normalizes region codes:

| Input | Normalized |
|-------|-----------|
| "india", "IN" | india |
| "us", "USA", "united states" | united_states |
| "uk", "GB", "united kingdom" | united_kingdom |
| "canada", "CA" | canada |
| "australia", "AU" | australia |

## Rate Limiting

The tool includes built-in rate limiting protection:

1. **Sleep between requests**: 1 second delay when fetching related queries
2. **Retry with backoff**: Exponential backoff on failures (2^attempt seconds)
3. **Error visibility**: Errors logged, not silently hidden
4. **Graceful degradation**: Returns empty arrays with error info if related queries fail

## Timeout Protection

External API calls can hang. The tool includes:

1. **Documentation**: Timeout considerations documented in code
2. **Future enhancement**: Can add timeout parameter to TrendReq initialization
3. **Production recommendation**: Use `requests` with timeout or signal-based timeouts

Example for production:
```python
from pytrends.request import TrendReq
# timeout=(connect_timeout, read_timeout)
pytrends = TrendReq(hl='en-US', tz=360, timeout=(10, 25))
```

## Score Field Explanation

**Important**: Google Trends API does not provide absolute popularity scores.

The tool returns:
- `rank`: Position in trending list (1-10, where 1 is most popular)
- `score`: Always `None` (API limitation)

The `rank` field serves as a proxy for relative popularity.

## Error Handling

The tool provides visibility into errors:

```python
try:
    result = tool.safe_execute(region="india", include_related=True)
    
    # Check for related query errors
    for trend in result['trends']:
        if trend['related_queries_error']:
            print(f"Warning: {trend['related_queries_error']}")
            
except Exception as e:
    print(f"Failed after retries: {e}")
```

Errors are not silently hidden - they're returned in the response for debugging.

## Integration with Processor Agent

The processor agent automatically detects trends intent:

```python
def _detect_intent(self, user_input: str, plan: Dict[str, Any]) -> str:
    input_lower = user_input.lower()
    
    trends_keywords = ['trend', 'trending', 'popular', 'viral', 'google trends']
    if any(keyword in input_lower for keyword in trends_keywords):
        return 'trends'
    
    return 'generic'
```

When trends intent detected:
1. Processor loads Google Trends tool from registry
2. Calls `safe_execute()` with region from state
3. Returns formatted trends data
4. Validator checks data quality

## Examples

See `examples/google_trends_example.py` for comprehensive examples:

```bash
python examples/google_trends_example.py
```

## Testing

Run tests:

```bash
pytest tests/test_google_trends_tool.py -v
```

Note: Integration tests are skipped by default to avoid rate limits.

## Best Practices

1. **Use safe_execute()** - Always use retry logic for production
2. **Respect rate limits** - Don't call too frequently (1s between requests)
3. **Cache results** - Consider caching for repeated queries
4. **Handle errors** - Always wrap in try/except and check error fields
5. **Set include_related=False** - For faster responses when related queries not needed
6. **Monitor timeouts** - Consider adding timeout protection for production
7. **Check error fields** - Inspect `related_queries_error` for debugging

## Intent Detection Limitations

The current intent detection is keyword-based and fragile:

```python
trends_keywords = ['trend', 'trending', 'popular', 'viral', 'google trends']
```

**Future improvements:**
- Use LLM for intent classification
- Train dedicated intent classifier
- Use embeddings for semantic matching
- Maintain intent history for context

For now, this simple approach works but may need enhancement as the system grows.

## Troubleshooting

**Rate limit errors:**
- Increase sleep time between requests
- Reduce number of topics fetched
- Use `include_related=False`

**Network errors:**
- Check internet connection
- Verify pytrends is installed
- Try different region

**Empty results:**
- Region might not be supported
- Try different region code
- Check pytrends documentation
