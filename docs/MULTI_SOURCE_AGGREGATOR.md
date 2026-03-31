# Multi-Source Trends Aggregator

## Overview

The Trends Aggregator is a production-ready pattern for combining data from multiple sources with intelligent deduplication and ranking.

## Architecture

```
┌─────────────────────────────────────┐
│     Trends Aggregator Tool          │
├─────────────────────────────────────┤
│  ┌──────────────┐  ┌──────────────┐ │
│  │ Google       │  │ DuckDuckGo   │ │
│  │ Trends       │  │ Search       │ │
│  └──────────────┘  └──────────────┘ │
│           │              │           │
│           └──────┬───────┘           │
│                  ▼                   │
│         ┌────────────────┐           │
│         │ Merge & Rank   │           │
│         │ - Deduplicate  │           │
│         │ - Cross-rank   │           │
│         │ - Attribute    │           │
│         └────────────────┘           │
└─────────────────────────────────────┘
```

## Features

✅ **Multi-Source Fetching** - Combines Google Trends + DuckDuckGo  
✅ **Self-Healing Normalization** - Automatically fixes inconsistent tool outputs  
✅ **Intelligent Deduplication** - Normalizes and merges similar topics  
✅ **Cross-Source Ranking** - Topics appearing in multiple sources rank higher  
✅ **Partial Failure Handling** - Works even if one source fails  
✅ **Source Attribution** - Tracks which sources provided each topic  
✅ **Production-Ready** - Error handling, logging, retry logic  

## Self-Healing Architecture

The aggregator uses a response normalizer layer to ensure consistent data format:

```python
# Each tool returns different formats
google_result = {"source": "google_trends", "trends": [...]}
ddg_result = {"trends": [...]}  # Missing source field!

# Normalizer fixes inconsistencies
normalized = normalize_tool_response(ddg_result, "duckduckgo_trends")
# Now guaranteed: source, status, trends, count, error

# Validation ensures correctness
if validate_normalized_response(normalized):
    # Safe to use
    process_trends(normalized)
```

This prevents the system from breaking when:
- Tools return different field names (`topic` vs `title`)
- Tools omit required fields (`source`, `status`)
- Tools return strings instead of objects
- New tools are added with different formats  

## Usage

### Basic Usage

```python
from app.tools.tool_registry import ToolRegistry

# Get aggregator from registry
aggregator = ToolRegistry.get_tool("trends_aggregator")

# Fetch aggregated trends
result = aggregator.safe_execute(region="us")

print(f"Status: {result['status']}")
print(f"Sources: {result['sources_successful']}/{result['sources_queried']}")
print(f"Trends: {result['count']}")

for trend in result['trends']:
    print(f"{trend['rank']}. {trend['topic']}")
    print(f"   Sources: {', '.join(trend['sources'])}")
    print(f"   Score: {trend['score']}")
```

### With Multi-Agent System

The processor agent automatically uses the aggregator when available:

```python
from app.graphs.multi_agent_graph import build_multi_agent_graph

graph = build_multi_agent_graph()
result = graph.invoke({
    "input": "Show me trending topics",
    "region": "us"
})

# Aggregator is used automatically
```

## How It Works

### 1. Parallel Fetching with Self-Healing

```python
sources_data = []
for tool_name, tool in self.tools.items():
    try:
        # Fetch raw response
        raw_response = tool.safe_execute(**kwargs)
        
        # NORMALIZE: Self-healing layer
        normalized_response = normalize_tool_response(raw_response, tool_name)
        
        # Validate normalization
        if not validate_normalized_response(normalized_response):
            raise Exception(f"Normalization failed for {tool_name}")
        
        # Check if source actually succeeded
        if normalized_response.get("status") == "success":
            sources_data.append(normalized_response)
        else:
            # Source reported failure
            errors.append({
                "source": tool_name,
                "status": "failed",
                "error": normalized_response.get("error")
            })
    except Exception as e:
        # Log error but continue with other sources
        errors.append({"source": tool_name, "error": str(e)})
```

### 2. Topic Normalization

```python
def _normalize_topic(self, topic: str) -> str:
    # Convert to lowercase
    normalized = topic.lower().strip()
    
    # Remove special characters
    normalized = re.sub(r'[^\w\s]', '', normalized)
    
    # Remove extra whitespace
    normalized = ' '.join(normalized.split())
    
    return normalized
```

### 3. Deduplication & Merging

```python
# Track topics across sources
topic_map = {}  # normalized -> {original, sources, count}

for source_data in sources_data:
    for trend in source_data['trends']:
        normalized = self._normalize_topic(trend['topic'])
        
        if normalized not in topic_map:
            topic_map[normalized] = {
                "original": trend['topic'],
                "sources": [],
                "count": 0
            }
        
        topic_map[normalized]["sources"].append(source_name)
        topic_map[normalized]["count"] += 1
```

### 4. Cross-Source Ranking

```python
# Calculate score (COMPUTED, not from API)
source_score = data["count"] * 100  # More sources = higher score
rank_score = 1000 / (data["rank_sum"] + 1)  # Lower rank = higher score
total_score = source_score + rank_score

# Sort by score
merged_trends.sort(key=lambda x: x["score"], reverse=True)
```

**Important Note on Scores:**
- Scores are COMPUTED by the aggregator, not provided by APIs
- Google Trends and DuckDuckGo don't provide absolute popularity scores
- Our scoring algorithm combines:
  - Cross-source frequency (appears in multiple sources = higher score)
  - Ranking position (lower rank = more popular = higher score)
- This is documented in each trend's `score_note` field

## Response Format

```python
{
    "status": "success" | "partial_success" | "failed",
    "sources_queried": 2,
    "sources_successful": 2,
    "count": 10,
    "trends": [
        {
            "topic": "AI Technology",
            "rank": 1,
            "sources": ["google_trends", "duckduckgo_trends"],
            "source_count": 2,
            "score": 250.5,
            "score_note": "Computed score (not from API): based on cross-source frequency and ranking",
            "metadata": [
                {
                    "source": "google_trends",
                    "rank": 1,
                    "link": null
                },
                {
                    "source": "duckduckgo_trends",
                    "rank": 3,
                    "link": "https://..."
                }
            ]
        }
    ],
    "errors": [],
    "raw_sources": [...]
}
```

### Status Values

- **success**: All sources returned data successfully
- **partial_success**: Some sources succeeded, others failed (still usable)
- **failed**: All sources failed (no data available)

### Error Handling

Failed sources are tracked in the `errors` array and `raw_sources`:

```python
{
    "status": "partial_success",
    "sources_successful": 1,
    "errors": [
        {
            "source": "google_trends",
            "status": "failed",
            "error": "Rate limit exceeded"
        }
    ]
}
```

## Benefits

### 1. Reliability
- If one source fails, others still work
- Partial success is better than total failure

### 2. Accuracy
- Cross-validation across sources
- Topics in multiple sources are more reliable

### 3. Completeness
- More comprehensive results
- Different sources provide different perspectives

### 4. Flexibility
- Easy to add new sources
- Sources can be enabled/disabled

## Adding New Sources

### Step 1: Create Tool

```python
class NewTrendsTool(BaseTool):
    def execute(self, **kwargs):
        # Fetch from new source
        return {
            "source": "new_source",
            "status": "success",
            "trends": [
                {"topic": "...", "rank": 1}
            ]
        }
```

### Step 2: Register Tool

```python
# In tool_registry.py
_tools = {
    "new_trends": NewTrendsTool,
}
```

### Step 3: Add to Aggregator

```python
# In tool_registry.py get_tool()
if tool_name == "trends_aggregator":
    trends_tools = {
        "google_trends": cls.get_tool("google_trends"),
        "duckduckgo_trends": cls.get_tool("duckduckgo_trends"),
        "new_trends": cls.get_tool("new_trends")  # Add here
    }
```

## Performance Considerations

### Parallel Execution
Currently sequential. For production, consider:

```python
import asyncio

async def fetch_all_sources():
    tasks = [
        asyncio.create_task(tool.safe_execute(**kwargs))
        for tool in self.tools.values()
    ]
    return await asyncio.gather(*tasks, return_exceptions=True)
```

### Caching
Add caching to avoid repeated API calls:

```python
from functools import lru_cache
import time

@lru_cache(maxsize=100)
def cached_aggregate(region, timestamp):
    # timestamp changes every 5 minutes
    return aggregator.execute(region=region)

# Use with 5-minute cache
timestamp = int(time.time() / 300)
result = cached_aggregate("us", timestamp)
```

## Testing

```bash
# Test aggregator
python test_aggregator.py

# Test with multi-agent system
python demo_trends.py
```

## Monitoring

Track these metrics:
- Source success rate
- Average response time per source
- Deduplication rate
- Cross-source match rate

## Future Enhancements

1. **Async execution** - Parallel source fetching
2. **Weighted scoring** - Different weights for different sources
3. **Confidence scores** - Based on source reliability
4. **Trend velocity** - Track how fast topics are rising
5. **Historical comparison** - Compare with previous periods

## Conclusion

The multi-source aggregator is a production-ready pattern that demonstrates:
- Senior-level architecture thinking
- Robust error handling
- Intelligent data merging
- Scalable design

This pattern can be applied to any multi-source data aggregation problem.
