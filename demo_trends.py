"""Demo: Multi-agent system with Google Trends integration"""

from app.graphs.multi_agent_graph import build_multi_agent_graph
from app.utils.logger import log_workflow_summary
import json


def demo_trends_integration():
    """Demonstrate Google Trends tool integration with multi-agent system"""
    
    print("🔥 Multi-Agent System + Google Trends Integration Demo\n")
    print("=" * 70)
    
    # Build graph
    graph = build_multi_agent_graph()
    
    # Test input requesting trends
    test_input = {
        "input": "Show me the trending topics on Google right now",
        "region": "united_states",  # Changed from india due to API limitations
        "execution_history": []
    }
    
    print(f"📥 User Request: {test_input['input']}")
    print(f"🌍 Region: {test_input['region']}")
    print(f"   Note: Using US region (India not supported by Google Trends API)\n")
    print("=" * 70 + "\n")
    
    print("⚙️  Executing multi-agent workflow...")
    print("   Coordinator → Processor (with Google Trends) → Validator\n")
    
    # Execute
    result = graph.invoke(test_input)
    
    # Show workflow summary
    log_workflow_summary(result)
    
    # Show trends data
    processed = result.get("processed_output", {})
    trends_data = processed.get("trends_data", {})
    
    if trends_data and "trends" in trends_data:
        print("📊 Trending Topics:\n")
        for i, trend in enumerate(trends_data["trends"][:5], 1):
            print(f"{i}. {trend['topic']}")
            if trend.get('related_queries'):
                print(f"   Related: {', '.join(trend['related_queries'][:3])}")
            print()
    
    print("=" * 70)
    print("🎯 Integration Features Demonstrated:")
    print("  ✅ Tool registry integration")
    print("  ✅ Intent detection (trends keyword)")
    print("  ✅ Real external API call (Google Trends)")
    print("  ✅ Rate limiting protection")
    print("  ✅ Error handling with retry logic")
    print("  ✅ Agent-driven tool selection")
    print("=" * 70)


if __name__ == "__main__":
    try:
        demo_trends_integration()
    except Exception as e:
        print(f"\n❌ Error: {e}")
        print("\nNote: This demo requires:")
        print("  1. pip install pytrends")
        print("  2. Network access to Google Trends API")
        print("  3. May hit rate limits if run repeatedly")
