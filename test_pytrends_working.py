"""Test pytrends with working endpoints"""

from pytrends.request import TrendReq
import pandas as pd

def test_interest_over_time():
    """Test interest_over_time - this endpoint works"""
    print("Testing interest_over_time (working endpoint)...\n")
    
    try:
        pytrends = TrendReq(hl='en-US', tz=360)
        
        # Build payload with popular keywords
        keywords = ["Python", "JavaScript", "AI", "ChatGPT", "React"]
        pytrends.build_payload(keywords, timeframe='now 7-d')
        
        # Get interest over time
        df = pytrends.interest_over_time()
        
        if not df.empty:
            print("✅ interest_over_time works!")
            print(f"\nKeywords analyzed: {', '.join(keywords)}")
            print(f"\nAverage interest (last 7 days):")
            
            avg_interest = df.mean().sort_values(ascending=False)
            for keyword, score in avg_interest.items():
                if keyword != 'isPartial':
                    print(f"  {keyword}: {score:.1f}")
            
            print(f"\nMost trending: {avg_interest.index[0]}")
            return True
        else:
            print("❌ No data returned")
            return False
            
    except Exception as e:
        print(f"❌ Error: {e}")
        return False


def test_related_queries():
    """Test related_queries - this endpoint works"""
    print("\n" + "="*60)
    print("Testing related_queries (working endpoint)...\n")
    
    try:
        pytrends = TrendReq(hl='en-US', tz=360)
        
        keyword = "Python"
        pytrends.build_payload([keyword], timeframe='now 7-d')
        
        related = pytrends.related_queries()
        
        if keyword in related and related[keyword]["top"] is not None:
            print(f"✅ related_queries works!")
            print(f"\nRelated queries for '{keyword}':")
            
            top_queries = related[keyword]["top"]["query"].tolist()[:5]
            for i, query in enumerate(top_queries, 1):
                print(f"  {i}. {query}")
            return True
        else:
            print("❌ No related queries found")
            return False
            
    except Exception as e:
        print(f"❌ Error: {e}")
        return False


def test_suggestions():
    """Test suggestions - this endpoint works"""
    print("\n" + "="*60)
    print("Testing suggestions (working endpoint)...\n")
    
    try:
        pytrends = TrendReq(hl='en-US', tz=360)
        
        keyword = "technology"
        suggestions = pytrends.suggestions(keyword=keyword)
        
        if suggestions:
            print(f"✅ suggestions works!")
            print(f"\nSuggestions for '{keyword}':")
            
            for i, suggestion in enumerate(suggestions[:5], 1):
                print(f"  {i}. {suggestion['title']} ({suggestion['type']})")
            return True
        else:
            print("❌ No suggestions found")
            return False
            
    except Exception as e:
        print(f"❌ Error: {e}")
        return False


if __name__ == "__main__":
    print("🔥 Testing PyTrends Working Endpoints\n")
    print("="*60)
    
    results = []
    results.append(("interest_over_time", test_interest_over_time()))
    results.append(("related_queries", test_related_queries()))
    results.append(("suggestions", test_suggestions()))
    
    print("\n" + "="*60)
    print("SUMMARY")
    print("="*60)
    
    for endpoint, success in results:
        status = "✅ Working" if success else "❌ Failed"
        print(f"{endpoint:20} {status}")
    
    working_count = sum(1 for _, success in results if success)
    print(f"\n{working_count}/{len(results)} endpoints working")
    
    if working_count > 0:
        print("\n✅ PyTrends has working endpoints we can use!")
    else:
        print("\n❌ All endpoints failed - check internet connection")
