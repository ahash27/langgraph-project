# Google Trends API Limitations

## Known Issues

### 1. Region Support is Inconsistent

**Problem**: Not all regions support the `trending_searches()` endpoint.

**Symptoms**:
- 404 errors for certain regions
- "Region not found" errors
- Empty results

**Affected Regions**:
- India (`india`) - Returns 404
- Many Asian countries
- Some European countries
- Most African countries

**Working Regions**:
✅ United States (`united_states`)  
✅ United Kingdom (`united_kingdom`)  
✅ Canada (`canada`)  
✅ Australia (`australia`)  
✅ Japan (`japan`)  
✅ Germany (`germany`)  
✅ France (`france`)  

**Workaround**:
```python
# Use supported region
tool.safe_execute(region="united_states")

# Or check if region is supported
if region in GoogleTrendsTool.SUPPORTED_REGIONS:
    result = tool.safe_execute(region=region)
else:
    # Fallback to US
    result = tool.safe_execute(region="united_states")
```

### 2. Rate Limiting

**Problem**: Google Trends aggressively rate limits requests.

**Symptoms**:
- 429 (Too Many Requests) errors
- Temporary bans (can last hours)
- Slow responses

**Mitigation**:
- Use `include_related=False` for faster responses
- Add delays between requests (1-2 seconds minimum)
- Implement caching
- Use exponential backoff on failures

**Example**:
```python
import time

# Fetch trends with rate limiting
result1 = tool.safe_execute(region="united_states")
time.sleep(2)  # Wait 2 seconds
result2 = tool.safe_execute(region="canada")
```

### 3. No Absolute Scores

**Problem**: API doesn't provide popularity scores.

**Impact**: Can't compare absolute popularity across topics.

**Workaround**: Use ranking (1-10) as relative popularity proxy.

### 4. Related Queries Can Fail

**Problem**: Related queries endpoint is less reliable.

**Symptoms**:
- Empty results
- Timeout errors
- 404 errors for valid keywords

**Mitigation**:
- Set `include_related=False` for critical paths
- Check `related_queries_error` field in response
- Implement fallback logic

### 5. API Changes Without Notice

**Problem**: Google can change API behavior anytime.

**Impact**:
- Previously working regions stop working
- Response format changes
- New rate limits

**Mitigation**:
- Monitor error rates
- Implement robust error handling
- Have fallback data sources
- Keep pytrends updated

## Recommendations

### For Production

1. **Use Supported Regions Only**
   ```python
   SUPPORTED_REGIONS = [
       "united_states",
       "united_kingdom",
       "canada",
       "australia"
   ]
   ```

2. **Implement Caching**
   ```python
   from functools import lru_cache
   import time
   
   @lru_cache(maxsize=100)
   def cached_trends(region, timestamp):
       # timestamp changes every 5 minutes
       return fetch_trends(region)
   
   # Use with 5-minute cache
   timestamp = int(time.time() / 300)
   result = cached_trends("united_states", timestamp)
   ```

3. **Add Circuit Breaker**
   ```python
   class CircuitBreaker:
       def __init__(self, failure_threshold=5):
           self.failures = 0
           self.threshold = failure_threshold
           self.is_open = False
       
       def call(self, func, *args, **kwargs):
           if self.is_open:
               raise Exception("Circuit breaker is open")
           
           try:
               result = func(*args, **kwargs)
               self.failures = 0
               return result
           except Exception as e:
               self.failures += 1
               if self.failures >= self.threshold:
                   self.is_open = True
               raise e
   ```

4. **Monitor and Alert**
   - Track error rates
   - Alert on sustained failures
   - Log API response times
   - Monitor rate limit hits

5. **Have Fallback Strategy**
   - Cache last successful results
   - Use alternative data sources
   - Provide graceful degradation

## Testing

When testing, be aware:

1. **Don't run tests repeatedly** - You'll hit rate limits
2. **Use mocks for CI/CD** - Don't call real API in tests
3. **Test with supported regions only**
4. **Expect occasional failures** - API is unreliable

## Alternative Data Sources

If Google Trends is too unreliable:

1. **Twitter Trending API** - More reliable, requires auth
2. **Reddit Hot Posts** - Free, no auth required
3. **News APIs** - NewsAPI, GDELT
4. **Social Media APIs** - Facebook, Instagram (require auth)

## Updates

This document reflects API behavior as of March 2026. Check pytrends GitHub issues for latest information:
https://github.com/GeneralMills/pytrends/issues
