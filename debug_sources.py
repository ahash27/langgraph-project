"""Debug script to check data structure from each source"""

from app.tools.tool_registry import ToolRegistry
import json

def debug_google_trends():
    """Check Google Trends data structure"""
    print("=" * 70)
    print("GOOGLE TRENDS DATA STRUCTURE")
    print("=" * 70)
    
    try:
        tool = ToolRegistry.get_tool("google_trends")
        result = tool.safe_execute(region="us")
        
        print(f"\nStatus: {result.get('status')}")
        print(f"Source: {result.get('source')}")
        print(f"Count: {result.get('count')}")
        print(f"\nFull structure:")
        print(json.dumps(result, indent=2, default=str))
        
        if result.get('trends'):
            print(f"\nFirst trend structure:")
            print(json.dumps(result['trends'][0], indent=2, default=str))
        
        return result
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()
        return None

def debug_duckduckgo():
    """Check DuckDuckGo data structure"""
    print("\n" + "=" * 70)
    print("DUCKDUCKGO DATA STRUCTURE")
    print("=" * 70)
    
    try:
        tool = ToolRegistry.get_tool("duckduckgo_trends")
        result = tool.safe_execute(region="us")
        
        print(f"\nStatus: {result.get('status')}")
        print(f"Source: {result.get('source')}")
        print(f"Count: {result.get('count')}")
        print(f"\nFull structure:")
        print(json.dumps(result, indent=2, default=str))
        
        if result.get('trends'):
            print(f"\nFirst trend structure:")
            print(json.dumps(result['trends'][0], indent=2, default=str))
        
        return result
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()
        return None

if __name__ == "__main__":
    print("🔍 Debugging Source Data Structures\n")
    
    google_data = debug_google_trends()
    ddg_data = debug_duckduckgo()
    
    print("\n" + "=" * 70)
    print("COMPARISON")
    print("=" * 70)
    
    if google_data and ddg_data:
        print(f"\nGoogle Trends has {len(google_data.get('trends', []))} trends")
        print(f"DuckDuckGo has {len(ddg_data.get('trends', []))} trends")
        
        if google_data.get('trends'):
            print(f"\nGoogle trend keys: {list(google_data['trends'][0].keys())}")
        if ddg_data.get('trends'):
            print(f"DuckDuckGo trend keys: {list(ddg_data['trends'][0].keys())}")
