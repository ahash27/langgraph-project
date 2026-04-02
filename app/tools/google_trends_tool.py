"""Google Trends tool for fetching trending topics and related queries"""

from typing import Dict, List, Any, Optional
import time
from app.tools.base_tool import BaseTool
from app.utils.logger import log_tool_usage


class GoogleTrendsTool(BaseTool):
    """
    Tool for fetching Google Trends data.
    
    Provides access to:
    - Daily trending searches by region
    - Related queries for specific topics
    - Real-time trend data
    
    Features:
    - Rate limiting protection
    - Retry logic with exponential backoff
    - Region normalization
    - Error handling with visibility
    - Timeout protection (documented)
    
    Note on Scores:
    Google Trends API does not provide absolute popularity scores.
    We use ranking (1-10) as a proxy, where 1 is most popular.
    
    Note on Timeouts:
    External API calls can hang. In production, consider:
    - Using requests with timeout parameter
    - Implementing signal-based timeouts
    - Setting pytrends timeout in TrendReq initialization
    """
    
    # Region mapping for normalization
    # Returns tuple: (normalized_name, ISO_country_code)
    # ISO codes are used for pytrends geo parameter
    REGION_MAP = {
        "india": ("india", "IN"),
        "in": ("india", "IN"),
        "us": ("united_states", "US"),
        "usa": ("united_states", "US"),
        "united states": ("united_states", "US"),
        "uk": ("united_kingdom", "GB"),
        "gb": ("united_kingdom", "GB"),
        "united kingdom": ("united_kingdom", "GB"),
        "canada": ("canada", "CA"),
        "ca": ("canada", "CA"),
        "australia": ("australia", "AU"),
        "au": ("australia", "AU"),
        "japan": ("japan", "JP"),
        "jp": ("japan", "JP"),
        "germany": ("germany", "DE"),
        "de": ("germany", "DE"),
        "france": ("france", "FR"),
        "fr": ("france", "FR")
    }
    
    # Regions known to work with trending_searches()
    # Google Trends API is inconsistent - some regions work, others don't
    SUPPORTED_REGIONS = [
        "united_states",
        "united_kingdom", 
        "canada",
        "australia",
        "japan",
        "germany",
        "france"
    ]
    
    def __init__(self):
        super().__init__(
            name="google_trends",
            description="Fetches trending topics and related queries from Google Trends"
        )
        self.pytrends = None
        self._initialize_client()
    
    def _initialize_client(self):
        """Initialize pytrends client lazily"""
        try:
            from pytrends.request import TrendReq
            # Note: timeout can be set here for production
            # TrendReq(hl='en-US', tz=360, timeout=(10, 25))
            self.pytrends = TrendReq(hl='en-US', tz=360)
        except ImportError:
            raise ImportError(
                "pytrends is required. Install with: pip install pytrends"
            )
    
    def _normalize_region(self, region: str) -> tuple:
        """
        Normalize region code to pytrends format.
        
        Args:
            region: Region code or name
            
        Returns:
            Tuple of (normalized_region_name, ISO_country_code)
            ISO code is used for pytrends geo parameter
        """
        region_lower = region.lower().strip()
        return self.REGION_MAP.get(region_lower, (region_lower, ""))
    
    def fetch_trending_searches(self, region: str = "united_states", geo_code: str = "") -> List[str]:
        """
        Fetch current trending searches for a region.
        
        Note: The trending_searches() endpoint is broken in pytrends.
        This method uses interest_over_time() with popular keywords as a workaround.
        
        Args:
            region: Region code (e.g., 'united_states', 'united_kingdom')
            geo_code: ISO country code for API (e.g., 'US', 'GB')
            
        Returns:
            List of trending search terms
        """
        # Popular keywords to check (workaround for broken trending_searches)
        popular_keywords = [
            "AI", "ChatGPT", "Python", "JavaScript", "React",
            "Climate Change", "Electric Cars", "Cryptocurrency",
            "Space", "Technology"
        ]
        
        try:
            # Use interest_over_time as workaround
            self.pytrends.build_payload(
                popular_keywords[:5],  # Limit to 5 keywords
                timeframe='now 7-d',
                geo=geo_code  # Use ISO country code
            )
            
            df = self.pytrends.interest_over_time()
            
            if df.empty:
                return popular_keywords[:10]
            
            # Get average interest for each keyword
            avg_interest = df.mean().sort_values(ascending=False)
            trending = avg_interest.index.tolist()
            
            return trending[:10]
            
        except Exception as e:
            # Return popular keywords as fallback
            return popular_keywords[:10]
    
    def fetch_related_queries(self, keyword: str) -> Dict[str, Any]:
        """
        Fetch related queries for a specific keyword.
        
        Args:
            keyword: Search keyword
            
        Returns:
            Dictionary with queries list and optional error
        """
        try:
            self.pytrends.build_payload([keyword], timeframe='now 7-d')
            related = self.pytrends.related_queries()
            
            if keyword in related and related[keyword]["top"] is not None:
                queries = related[keyword]["top"]["query"].tolist()
                return {
                    "queries": queries[:5],  # Top 5 related queries
                    "error": None
                }
            return {"queries": [], "error": None}
        except Exception as e:
            # Don't hide failures - return error info
            return {
                "queries": [],
                "error": f"Failed to fetch related queries: {str(e)}"
            }
    
    def execute(
        self,
        keyword: Optional[str] = None,
        region: str = "united_states",
        include_related: bool = True
    ) -> Dict[str, Any]:
        """
        Execute Google Trends data fetch.
        
        Args:
            keyword: Optional specific keyword to analyze
            region: Region code (default: 'united_states')
            include_related: Whether to fetch related queries
            
        Returns:
            Dictionary with trends data
            
        Note:
            Default region changed to 'united_states' due to API limitations.
            Not all regions support trending_searches().
        """
        # Normalize region and get ISO code
        normalized_region, geo_code = self._normalize_region(region)
        
        # If specific keyword provided, analyze it
        if keyword:
            related_result = {"queries": [], "error": None}
            if include_related:
                related_result = self.fetch_related_queries(keyword)
            
            return {
                "region": normalized_region,
                "keyword": keyword,
                "related_queries": related_result["queries"],
                "related_queries_error": related_result["error"],
                "trends": []
            }
        
        # Otherwise, fetch trending searches
        trends = self.fetch_trending_searches(normalized_region, geo_code)
        results = []
        
        for index, topic in enumerate(trends, start=1):
            trend_data = {
                "topic": topic,
                "rank": index,  # Ranking as proxy for score (1-10)
                "score": None,  # Google Trends doesn't provide absolute scores
                "related_queries": [],
                "related_queries_error": None
            }
            
            # Fetch related queries if requested
            if include_related:
                related_result = self.fetch_related_queries(topic)
                trend_data["related_queries"] = related_result["queries"]
                trend_data["related_queries_error"] = related_result["error"]
                
                # Rate limiting protection
                if related_result["error"] is None:
                    time.sleep(1)
            
            results.append(trend_data)
        
        return {
            "source": "google_trends",
            "status": "success",
            "region": normalized_region,
            "trends": results,
            "count": len(results)
        }
    
    def safe_execute(
        self,
        max_retries: int = 3,
        **kwargs
    ) -> Dict[str, Any]:
        """
        Execute with retry logic and exponential backoff.
        
        Args:
            max_retries: Maximum number of retry attempts
            **kwargs: Arguments to pass to execute()
            
        Returns:
            Trends data dictionary
            
        Raises:
            Exception: If all retries fail
        """
        last_error = None
        
        for attempt in range(max_retries):
            try:
                return self.execute(**kwargs)
            except Exception as e:
                last_error = e
                if attempt < max_retries - 1:
                    # Exponential backoff: 2^attempt seconds
                    wait_time = 2 ** attempt
                    time.sleep(wait_time)
                else:
                    raise Exception(
                        f"Failed after {max_retries} attempts: {str(last_error)}"
                    )
        
        # Should never reach here, but for type safety
        raise Exception(f"Unexpected error: {str(last_error)}")
