"""Multi-source trends aggregator tool"""

from typing import Dict, List, Any, Optional
from collections import Counter
from app.tools.base_tool import BaseTool
from app.utils.logger import log_tool_usage
import re


class TrendsAggregatorTool(BaseTool):
    """
    Aggregates trends from multiple sources.
    
    Features:
    - Combines results from Google Trends and DuckDuckGo
    - Removes duplicates
    - Ranks by frequency across sources
    - Provides source attribution
    - Handles partial failures gracefully
    
    This is a production-ready pattern for multi-source data aggregation.
    """
    
    def __init__(self, tools: Dict[str, Any]):
        super().__init__(
            name="trends_aggregator",
            description="Aggregates trending topics from multiple sources"
        )
        self.tools = tools
    
    def _normalize_topic(self, topic: str) -> str:
        """
        Normalize topic string for comparison.
        
        Args:
            topic: Raw topic string
            
        Returns:
            Normalized topic string
        """
        # Convert to lowercase
        normalized = topic.lower().strip()
        
        # Remove special characters
        normalized = re.sub(r'[^\w\s]', '', normalized)
        
        # Remove extra whitespace
        normalized = ' '.join(normalized.split())
        
        return normalized
    
    def _merge_and_rank(
        self, 
        sources_data: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """
        Merge results from multiple sources and rank by frequency.
        
        Args:
            sources_data: List of results from different sources
            
        Returns:
            Merged and ranked trends
        """
        # Track topics and their sources
        topic_map = {}  # normalized_topic -> {original, sources, count}
        
        for source_data in sources_data:
            if source_data.get("status") != "success":
                continue
            
            source_name = source_data.get("source", "unknown")
            trends = source_data.get("trends", [])
            
            for trend in trends:
                topic = trend.get("topic", "")
                if not topic:
                    continue
                
                normalized = self._normalize_topic(topic)
                
                if normalized not in topic_map:
                    topic_map[normalized] = {
                        "original": topic,
                        "normalized": normalized,
                        "sources": [],
                        "count": 0,
                        "rank_sum": 0,
                        "metadata": []
                    }
                
                # Add source
                topic_map[normalized]["sources"].append(source_name)
                topic_map[normalized]["count"] += 1
                
                # Add rank (lower is better)
                if "rank" in trend:
                    topic_map[normalized]["rank_sum"] += trend["rank"]
                
                # Store metadata
                topic_map[normalized]["metadata"].append({
                    "source": source_name,
                    "rank": trend.get("rank"),
                    "link": trend.get("link"),
                    "description": trend.get("description")
                })
        
        # Convert to list and sort
        merged_trends = []
        for normalized, data in topic_map.items():
            # Calculate score (higher is better)
            # More sources = higher score
            # Lower rank sum = higher score
            source_score = data["count"] * 100
            rank_score = 1000 / (data["rank_sum"] + 1) if data["rank_sum"] > 0 else 0
            total_score = source_score + rank_score
            
            merged_trends.append({
                "topic": data["original"],
                "normalized": normalized,
                "sources": list(set(data["sources"])),  # Unique sources
                "source_count": data["count"],
                "score": total_score,
                "metadata": data["metadata"]
            })
        
        # Sort by score (descending)
        merged_trends.sort(key=lambda x: x["score"], reverse=True)
        
        # Add final rank
        for idx, trend in enumerate(merged_trends, start=1):
            trend["rank"] = idx
        
        return merged_trends
    
    def execute(
        self,
        keyword: Optional[str] = None,
        region: str = "us",
        max_results: int = 10
    ) -> Dict[str, Any]:
        """
        Execute multi-source trends aggregation.
        
        Args:
            keyword: Optional specific keyword
            region: Region code
            max_results: Maximum results per source
            
        Returns:
            Aggregated trends data
        """
        sources_data = []
        errors = []
        
        # Fetch from each source
        for tool_name, tool in self.tools.items():
            try:
                # Build kwargs based on tool type
                tool_kwargs = {"region": region}
                
                # Google Trends specific params
                if tool_name == "google_trends":
                    tool_kwargs["include_related"] = False
                    if keyword:
                        tool_kwargs["keyword"] = keyword
                
                # DuckDuckGo specific params
                elif tool_name == "duckduckgo_trends":
                    tool_kwargs["max_results"] = max_results
                    if keyword:
                        tool_kwargs["keyword"] = keyword
                
                result = tool.safe_execute(**tool_kwargs)
                sources_data.append(result)
                log_tool_usage("aggregator", tool_name, success=True)
                
            except Exception as e:
                error_info = {
                    "source": tool_name,
                    "status": "failed",
                    "error": str(e)
                }
                sources_data.append(error_info)
                errors.append(error_info)
                log_tool_usage("aggregator", tool_name, success=False)
        
        # Merge and rank results
        merged_trends = self._merge_and_rank(sources_data)
        
        # Limit to max_results
        merged_trends = merged_trends[:max_results]
        
        # Determine overall status
        successful_sources = sum(
            1 for s in sources_data if s.get("status") == "success"
        )
        
        if successful_sources == 0:
            status = "failed"
        elif successful_sources < len(self.tools):
            status = "partial_success"
        else:
            status = "success"
        
        return {
            "status": status,
            "sources_queried": len(self.tools),
            "sources_successful": successful_sources,
            "count": len(merged_trends),
            "trends": merged_trends,
            "errors": errors,
            "raw_sources": sources_data
        }
    
    def safe_execute(
        self,
        max_retries: int = 1,  # Aggregator doesn't need many retries
        **kwargs
    ) -> Dict[str, Any]:
        """
        Execute with minimal retry (sources handle their own retries).
        
        Args:
            max_retries: Maximum retry attempts
            **kwargs: Arguments to pass to execute()
            
        Returns:
            Aggregated trends data
        """
        try:
            return self.execute(**kwargs)
        except Exception as e:
            raise Exception(f"Aggregator failed: {str(e)}")
