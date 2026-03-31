"""Example usage of Google Trends tool"""

from app.tools.google_trends_tool import GoogleTrendsTool
from app.tools.tool_registry import ToolRegistry
import json


def example_basic_usage():
    """Basic usage example"""
    print("=" * 70)
    print("Example 1: Basic Trending Searches")
    print("=" * 70)
    
    tool = GoogleTrendsTool()
    
    # Fetch trending searches for India
    result = tool.safe_execute(region="india", include_related=False)
    
    print(f"\nRegion: {result['region']}")
    print(f"Found {result['count']} trending topics:\n")
    
    for i, trend in enumerate(result['trends'][:5], 1):
        print(f"{i}. {trend['topic']}")


def example_with_related_queries():
    """Example with related queries"""
    print("\n" + "=" * 70)
    print("Example 2: Trends with Related Queries")
    print("=" * 70)
    
    tool = GoogleTrendsTool()
    
    # Fetch with related queries (slower due to rate limiting)
    result = tool.safe_execute(region="us", include_related=True)
    
    print(f"\nRegion: {result['region']}")
    print(f"Top 3 trends with related queries:\n")
    
    for i, trend in enumerate(result['trends'][:3], 1):
        print(f"\n{i}. {trend['topic']}")
        if trend['related_queries']:
            print(f"   Related: {', '.join(trend['related_queries'][:3])}")


def example_specific_keyword():
    """Example analyzing specific keyword"""
    print("\n" + "=" * 70)
    print("Example 3: Analyze Specific Keyword")
    print("=" * 70)
    
    tool = GoogleTrendsTool()
    
    # Analyze specific keyword
    result = tool.safe_execute(
        keyword="artificial intelligence",
        region="us",
        include_related=True
    )
    
    print(f"\nKeyword: {result['keyword']}")
    print(f"Region: {result['region']}")
    print(f"\nRelated Queries:")
    for query in result['related_queries']:
        print(f"  - {query}")


def example_via_registry():
    """Example using tool registry"""
    print("\n" + "=" * 70)
    print("Example 4: Using Tool Registry")
    print("=" * 70)
    
    # Get tool from registry
    tool = ToolRegistry.get_tool("google_trends")
    
    result = tool.safe_execute(region="india", include_related=False)
    
    print(f"\nTool: {tool.name}")
    print(f"Description: {tool.description}")
    print(f"\nResult: {json.dumps(result, indent=2)}")


def example_region_normalization():
    """Example showing region normalization"""
    print("\n" + "=" * 70)
    print("Example 5: Region Normalization")
    print("=" * 70)
    
    tool = GoogleTrendsTool()
    
    regions = ["india", "IN", "us", "USA", "uk", "GB"]
    
    print("\nRegion normalization:")
    for region in regions:
        normalized = tool._normalize_region(region)
        print(f"  {region:10} → {normalized}")


if __name__ == "__main__":
    print("\n🔥 Google Trends Tool Examples\n")
    
    try:
        example_basic_usage()
        # Uncomment to run other examples (they make API calls)
        # example_with_related_queries()
        # example_specific_keyword()
        # example_via_registry()
        example_region_normalization()
        
        print("\n" + "=" * 70)
        print("✅ Examples completed!")
        print("=" * 70)
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
        print("\nNote: Some examples require network access and may hit rate limits.")
        print("Run examples individually to avoid rate limiting.")
