# Future Improvements

This document tracks known limitations and planned enhancements for the multi-agent system.

## High Priority

### 1. Intent Detection Enhancement
**Current State**: Keyword-based detection (fragile)
```python
trends_keywords = ['trend', 'trending', 'popular', 'viral']
```

**Limitations**:
- Misses semantic variations
- No context awareness
- Can't handle ambiguous queries

**Proposed Solutions**:
- **Option A**: Use LLM for intent classification
  ```python
  intent = llm.classify_intent(user_input, available_intents)
  ```
- **Option B**: Train dedicated intent classifier
  - Use labeled dataset
  - Fine-tune small model (BERT, DistilBERT)
  - Fast inference, no API calls
- **Option C**: Embedding-based semantic matching
  - Compute embeddings for user input
  - Match against intent embeddings
  - Threshold-based classification

**Recommendation**: Start with Option A (LLM), migrate to Option B for production.

### 2. Timeout Protection for External APIs
**Current State**: Documented but not implemented

**Risk**: External API calls can hang indefinitely

**Proposed Solutions**:
- **Option A**: Add timeout to pytrends initialization
  ```python
  TrendReq(hl='en-US', tz=360, timeout=(10, 25))
  ```
- **Option B**: Wrap calls with signal-based timeout
  ```python
  import signal
  
  def timeout_handler(signum, frame):
      raise TimeoutError("API call timed out")
  
  signal.signal(signal.SIGALRM, timeout_handler)
  signal.alarm(30)  # 30 second timeout
  ```
- **Option C**: Use asyncio with timeout
  ```python
  async with asyncio.timeout(30):
      result = await fetch_trends()
  ```

**Recommendation**: Option A for simplicity, Option C for async architecture.

### 3. Caching Layer
**Current State**: No caching, every request hits API

**Impact**:
- Rate limiting issues
- Slower responses
- Unnecessary API calls

**Proposed Solutions**:
- **Option A**: In-memory cache with TTL
  ```python
  from functools import lru_cache
  import time
  
  @lru_cache(maxsize=100)
  def cached_trends(region, timestamp):
      return fetch_trends(region)
  ```
- **Option B**: Redis cache
  - Shared across instances
  - Configurable TTL
  - Persistence
- **Option C**: Database cache
  - Store trends with timestamp
  - Query recent results first

**Recommendation**: Option A for MVP, Option B for production scale.

## Medium Priority

### 4. Enhanced Error Recovery
**Current State**: Retry with exponential backoff

**Enhancements**:
- Circuit breaker pattern
- Fallback to cached data
- Graceful degradation strategies
- Error rate monitoring

### 5. Observability Improvements
**Current State**: Basic logging with timestamps

**Enhancements**:
- Structured logging (JSON format)
- Distributed tracing (OpenTelemetry)
- Metrics collection (Prometheus)
- Performance monitoring
- Error tracking (Sentry)

### 6. Agent Collaboration
**Current State**: Linear flow with retry loop

**Enhancements**:
- Parallel agent execution
- Agent-to-agent communication
- Shared memory/context
- Dynamic agent spawning

### 7. Tool Composition
**Current State**: Tools used independently

**Enhancements**:
- Tool chaining
- Tool pipelines
- Conditional tool execution
- Tool result caching

## Low Priority

### 8. Multi-Region Support
**Current State**: Single region per request

**Enhancement**: Fetch trends from multiple regions in parallel

### 9. Historical Trends
**Current State**: Only current trends

**Enhancement**: Support historical trend analysis

### 10. Trend Prediction
**Current State**: Reactive (current trends only)

**Enhancement**: Predictive analytics for emerging trends

## Implementation Roadmap

### Phase 1 (Immediate)
- [ ] Add timeout protection (High Priority #2)
- [ ] Implement basic caching (High Priority #3)
- [ ] Document intent detection limitations

### Phase 2 (Next Sprint)
- [ ] Enhance intent detection with LLM (High Priority #1)
- [ ] Add circuit breaker pattern (Medium Priority #4)
- [ ] Implement structured logging (Medium Priority #5)

### Phase 3 (Future)
- [ ] Agent collaboration features (Medium Priority #6)
- [ ] Tool composition (Medium Priority #7)
- [ ] Multi-region support (Low Priority #8)

## Contributing

When implementing improvements:
1. Update this document with progress
2. Add tests for new features
3. Update relevant documentation
4. Consider backward compatibility
5. Measure performance impact
