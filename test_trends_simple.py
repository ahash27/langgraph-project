"""Simple test to debug Google Trends API"""

from app.tools.google_trends_tool import GoogleTrendsTool
import traceback

def test_basic():
    """Test basic Google Trends functionality"""
    print("Testing Google Trends Tool...\n")
    
    try:
        tool = GoogleTrendsTool()
        print("✓ Tool initialized successfully")
        print(f"  Tool name: {tool.name}")
        print(f"  PyTrends client: {tool.pytrends is not None}\n")
        
        # Test region normalization
        print("Testing region normalization:")
        regions = ["india", "IN", "us", "USA"]
        for region in regions:
            normalized = tool._normalize_region(region)
            print(f"  {region:10} → {normalized}")
        print()
        
        # Test trending searches (without related queries)
        print("Fetching trending searches for India...")
        trends = tool.fetch_trending_searches(region="india")
        print(f"✓ Found {len(trends)} trends:")
        for i, trend in enumerate(trends[:5], 1):
            print(f"  {i}. {trend}")
        print()
        
        # Test full execute
        print("Testing full execute method...")
        result = tool.execute(region="india", include_related=False)
        print(f"✓ Execute successful:")
        print(f"  Region: {result['region']}")
        print(f"  Count: {result['count']}")
        print(f"  Trends: {len(result['trends'])}")
        print()
        
        # Test safe_execute
        print("Testing safe_execute with retry logic...")
        result = tool.safe_execute(region="india", include_related=False)
        print(f"✓ Safe execute successful:")
        print(f"  Region: {result['region']}")
        print(f"  Count: {result['count']}")
        
        print("\n" + "=" * 60)
        print("✅ All tests passed!")
        print("=" * 60)
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
        print("\nFull traceback:")
        traceback.print_exc()
        
        print("\n" + "=" * 60)
        print("Troubleshooting tips:")
        print("1. Check internet connection")
        print("2. Verify pytrends is installed: pip install pytrends")
        print("3. Try different region: 'united_states' instead of 'india'")
        print("4. Google Trends may be rate limiting - wait a few minutes")
        print("=" * 60)

if __name__ == "__main__":
    test_basic()
