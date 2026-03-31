"""Google Trends tool for fetching trending topics and related queries"""

from typing import Dict, List, Any, Optional
import time
from app.tools.base_tool import BaseTool


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
    - Error handling
    """
    
    # Region mapping for normalization
    REGION_MAP = {
        "india": "india",
        "in": "india",
        "us": "united_states",
        "usa": "united_states",
        "united states": "united_states",
        "uk": "united_kingdom",
        "gb": "united_kingdom",
        "united kingdom": "united_kingdom",
        "canada": "canada",
        "ca": "canada",
        "australia": "australia",
        "au": "australia"
    }
    
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
            self.pytrends = TrendReq(hl='en-US', tz=360)
        except ImportError:
            raise ImportError(
                "pytrends is required. Install with: pip install pytrends"
            )
    
    def _normalize_region(self, region: str) -> str:
        """
        Normalize region code to pytrends format.
        
        Args:
            region: Region code or name
            
        Returns:
            Normalized region code
        """
        region_lower = region.lower().strip()
        return self.REGION_MAP.get(region_lower, region_lower)
    
    def fetch_trending_searches(self, region: str = "india") -> List[str]:
        """
        Fetch current trending searches for a region.
        
        Args:
            region: Region code (e.g., 'india', 'united_states')
            
        Returns:
            List of trending search terms
        """
        try:
            df = self.pytrends.trending_searches(pn=region)
            return df[0].tolist()[:10]  # Top 10 trends
        except Exception as e:
            raise Exception(f"Error fetching trending searches: {str(e)}")
    
    def fetch_related_queries(self, keyword: str) -> List[str]:
        """
        Fetch related queries for a specific keyword.
        
        Args:
            keyword: Search keyword
            
        Returns:
            List of related query strings
        """
        try:
            self.pytrends.build_payload([keyword], timeframe='now 7-d')
            related = self.pytrends.related_queries()
            
            if keyword in related and related[keyword]["top"] is not None:
                queries = related[keyword]["top"]["query"].tolist()
                return queries[:5]  # Top 5 related queries
            return []
        except Exception:
            return []  # Gracefully handle errors for related queries
    
    def execute(
        self,
        keyword: Optional[str] = None,
        region: str = "india",
        include_related: bool = True
    ) -> Dict[str, Any]:
        """
        Execute Google Trends data fetch.
        
        Args:
            keyword: Optional specific keyword to analyze
            region: Region code (default: 'india')
            include_related: Whether to fetch related queries
            
        Returns:
            Dictionary with trends data
        """
        # Normalize region
        normalized_region = self._normalize_region(region)
        
        # If specific keyword provided, analyze it
        if keyword:
            related_queries = []
            if include_related:
                related_queries = self.fetch_related_queries(keyword)
            
            return {
                "region": normalized_region,
                "keyword": keyword,
                "related_queries": related_queries,
                "trends": []
            }
        
        # Otherwise, fetch trending searches
        trends = self.fetch_trending_searches(normalized_region)
        results = []
        
        for topic in trends:
            trend_data = {
                "topic": topic,
                "score": None,  # Google Trends doesn't provide direct scores
                "related_queries": []
            }
            
            # Fetch related queries if requested
            if include_related:
                try:
                    trend_data["related_queries"] = self.fetch_related_queries(topic)
                    time.sleep(1)  # Rate limiting protection
                except Exception:
                    pass  # Continue even if related queries fail
            
            results.append(trend_data)
        
        return {
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
