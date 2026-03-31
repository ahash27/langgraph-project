# How to Create the Pull Request

## Step 1: Go to GitHub

Visit: https://github.com/ahash27/langgraph-project/pull/new/feature/trends-aggregator

Or:
1. Go to https://github.com/ahash27/langgraph-project
2. Click "Compare & pull request" button (should appear at the top)

## Step 2: Fill in PR Details

### Title:
```
Multi-source trends aggregator with self-healing normalization
```

### Description:
```markdown
## Overview

Implemented a production-ready multi-source trends aggregation system with resilient architecture, self-healing normalization, and comprehensive error handling.

## Key Features

### 🔥 Self-Healing Response Normalizer
- Ensures consistent format across all tools
- Handles missing fields, string trends, title→topic conversion
- Validation layer for safety
- System won't break when tools return different formats

### 🌐 Google Trends Integration (pytrends)
- Production-ready wrapper with rate limiting and retry logic
- Fallback strategy: uses working `interest_over_time()` endpoint
- Region normalization and comprehensive error handling
- Integrated with processor agent via intent detection

### 🦆 DuckDuckGo Trends Tool
- No API key required
- Reliable search-based trend extraction
- Fast and simple implementation

### 🎯 Multi-Source Aggregator
- Combines results from Google Trends + DuckDuckGo
- Intelligent deduplication with topic normalization
- Cross-source ranking (topics in multiple sources rank higher)
- Partial failure handling (works even if one source fails)
- Source attribution and metadata tracking
- Computed scoring with clear documentation

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
│         │  Normalizer    │           │
│         │  (Self-Heal)   │           │
│         └────────────────┘           │
│                  ▼                   │
│         ┌────────────────┐           │
│         │ Merge & Rank   │           │
│         │ - Deduplicate  │           │
│         │ - Cross-rank   │           │
│         │ - Attribute    │           │
│         └────────────────┘           │
└─────────────────────────────────────┘
```

## Status Handling

- **success**: All sources returned data successfully
- **partial_success**: Some sources succeeded, others failed (still usable)
- **failed**: All sources failed (no data available)

## Score Computation

**Important:** Scores are COMPUTED by the aggregator, not provided by APIs.

Scoring algorithm:
- Source score: 100 points per source (cross-source frequency)
- Rank score: 1000 / (rank_sum + 1) (lower rank = higher score)

This is clearly documented in each trend's `score_note` field.

## Testing

All features tested and verified:

```bash
# Test aggregator
python test_aggregator.py

# Test with multi-agent system
python demo_trends.py

# Unit tests
pytest tests/test_response_normalizer.py
```

## Production-Ready Features

✅ Rate limiting protection  
✅ Retry logic with exponential backoff  
✅ Comprehensive error handling  
✅ Partial failure resilience  
✅ Self-healing normalization  
✅ Structured logging  
✅ Validation layers  
✅ Extensive documentation  

## Files Changed

**New Files:**
- `app/tools/google_trends_tool.py` - Google Trends wrapper
- `app/tools/duckduckgo_trends_tool.py` - DuckDuckGo trends tool
- `app/tools/trends_aggregator.py` - Multi-source aggregator
- `app/tools/response_normalizer.py` - Self-healing normalizer ⭐
- `tests/test_response_normalizer.py` - Normalizer tests
- `tests/test_google_trends_tool.py` - Google Trends tests
- 5 comprehensive documentation files in `docs/`

**Modified Files:**
- `app/agents/processor_agent.py` - Intent detection
- `app/tools/tool_registry.py` - Tool registration
- `requirements.txt` - Dependencies

## Dependencies Added

```
pytrends>=4.9.0
duckduckgo-search>=3.9.0
```

---

**PR ready for review.** Let me know if you'd like any changes or if I should extend this with additional sources.
```

## Step 3: Set Base and Compare

- **Base:** `main`
- **Compare:** `feature/trends-aggregator`

## Step 4: Create Pull Request

Click "Create pull request" button

## Step 5: Add Comment (Optional but Recommended)

After creating the PR, add a comment:

```
PR ready for review. Let me know if you'd like any changes or if I should extend this with additional sources.
```

---

## Quick Link

Direct link to create PR:
https://github.com/ahash27/langgraph-project/compare/main...feature/trends-aggregator
