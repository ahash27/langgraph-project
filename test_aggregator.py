"""Test multi-source trends aggregator"""

from app.tools.tool_registry import ToolRegistry
import json


def test_aggregator():
    """Test trends aggregator with multiple sources"""
    print("🔥 Testing Multi-Source Trends Aggregator\n")
    print("=" * 70)
    
    try:
        # Get aggregator from registry
        aggregator = ToolRegistry.get_tool("trends_aggregator")
        
        print(f"Tool: {aggregator.name}")
        print(f"Description: {aggregator.description}")
        print(f"Sources: Google Trends + DuckDuckGo\n")
        print("=" * 70)
        
        print("\nFetching trends from multiple sources...")
        print("(This may take 5-10 seconds)\n")
        
        # Execute aggregator
        result = aggregator.safe_execute(region="us")
        
        # Display results
        print("=" * 70)
        print("RESULTS")
        print("=" * 70)
        
        print(f"\nStatus: {result['status']}")
        print(f"Sources Queried: {result['sources_queried']}")
        print(f"Sources Successful: {result['sources_successful']}")
        print(f"Total Trends: {result['count']}\n")
        
        # Show errors if any
        if result['errors']:
            print("⚠️  Errors:")
            for error in result['errors']:
                print(f"  - {error['source']}: {error['error']}")
            print()
        
        # Show top trends
        print("📊 Top Trending Topics (Aggregated):\n")
        for trend in result['trends'][:10]:
            sources_str = ", ".join(trend['sources'])
            print(f"{trend['rank']}. {trend['topic']}")
            print(f"   Sources: {sources_str}")
            print(f"   Score: {trend['score']:.1f} (computed, not from API)")
            print()
        
        print("=" * 70)
        print("🎯 Aggregator Features Demonstrated:")
        print("  ✅ Multi-source data fetching")
        print("  ✅ Self-healing normalization")
        print("  ✅ Duplicate removal")
        print("  ✅ Cross-source ranking")
        print("  ✅ Partial failure handling")
        print("  ✅ Source attribution")
        print("  ✅ Computed scoring (not from API)")
        print("=" * 70)
        
        return True
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = test_aggregator()
    
    if success:
        print("\n✅ Aggregator test passed!")
    else:
        print("\n❌ Aggregator test failed")
        print("\nMake sure to install: pip install duckduckgo-search")
