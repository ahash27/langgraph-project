"""DuckDuckGo trends tool for fetching trending topics via search"""

from typing import Dict, List, Any, Optional
import time
from app.tools.base_tool import BaseTool
from app.utils.logger import log_tool_usage


class DuckDuckGoTrendsTool(BaseTool):
    """
    Tool for fetching trending topics using DuckDuckGo search.
    
    Features:
    - No API key required
    - No rate limiting issues
    - Real-time search results
    - Reliable and fast
    
    Note:
    DuckDuckGo doesn't have a dedicated trends API, but we can
    search for trending topics and extract relevant results.
    """
    
    def __init__(self):
        super().__init__(
            name="duckduckgo_trends",
            description="Fetches trending topics using DuckDuckGo search"
        )
        self.ddgs = None
        self._initialize_client()
    
    def _initialize_client(self):
        """Initialize DuckDuckGo search client"""
        try:
            from duckduckgo_search import DDGS
            self.ddgs = DDGS
        except ImportError:
            raise ImportError(
                "duckduckgo-search is required. Install with: pip install duckduckgo-search"
            )
    
    def fetch_trending_topics(
        self, 
        keyword: str = "trending topics today",
        max_results: int = 10
    ) -> List[Dict[str, Any]]:
        """
        Fetch trending topics via DuckDuckGo search.
        
        Args:
            keyword: Search query
            max_results: Maximum number of results
            
        Returns:
            List of trending topics with metadata
        """
        results = []
        
        try:
            with self.ddgs() as ddgs:
                search_results = ddgs.text(keyword, max_results=max_results)
                
                for idx, item in enumerate(search_results, start=1):
                    results.append({
                        "topic": item.get("title", ""),
                        "description": item.get("body", ""),
                        "source": "duckduckgo",
                        "link": item.get("href", ""),
                        "rank": idx
                    })
            
            return results
            
        except Exception as e:
            raise Exception(f"Error fetching from DuckDuckGo: {str(e)}")
    
    def execute(
        self,
        keyword: Optional[str] = None,
        region: str = "us",
        max_results: int = 10
    ) -> Dict[str, Any]:
        """
        Execute DuckDuckGo trends search.
        
        Args:
            keyword: Optional specific keyword to search
            region: Region code (not used by DDG, kept for compatibility)
            max_results: Maximum number of results
            
        Returns:
            Dictionary with trends data
        """
        # Build search query
        if keyword:
            search_query = f"{keyword} trending"
        else:
            search_query = "trending topics today"
        
        # Fetch results
        trends = self.fetch_trending_topics(search_query, max_results)
        
        return {
            "source": "duckduckgo",
            "status": "success",
            "query": search_query,
            "count": len(trends),
            "trends": trends
        }
    
    def safe_execute(
        self,
        max_retries: int = 3,
        **kwargs
    ) -> Dict[str, Any]:
        """
        Execute with retry logic.
        
        Args:
            max_retries: Maximum number of retry attempts
            **kwargs: Arguments to pass to execute()
            
        Returns:
            Trends data dictionary
        """
        last_error = None
        
        for attempt in range(max_retries):
            try:
                return self.execute(**kwargs)
            except Exception as e:
                last_error = e
                if attempt < max_retries - 1:
                    wait_time = 2 ** attempt
                    time.sleep(wait_time)
                else:
                    raise Exception(
                        f"Failed after {max_retries} attempts: {str(last_error)}"
                    )
        
        raise Exception(f"Unexpected error: {str(last_error)}")
