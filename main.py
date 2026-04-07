"""Entry point for testing multi-agent system"""

from app.graphs.multi_agent_graph import build_multi_agent_graph
from app.graphs.agent_registry import AgentRegistry
from app.tools.tool_registry import ToolRegistry
from app.utils.logger import log_workflow_summary
import json


def main():
    """Run multi-agent workflow with dynamic routing and observability"""
    try:
        print("🚀 Starting Multi-Agent System with Dynamic Routing & Observability...\n")
        
        # Show available agents and tools
        print("📋 Available Agents:", AgentRegistry.list_agents())
        print("🔧 Available Tools:", ToolRegistry.list_tools())
        print("\n" + "=" * 70 + "\n")
        
        # Build multi-agent graph with conditional routing
        graph = build_multi_agent_graph()
        
        # Test input
        test_input = {
            "input": "Process this generic task through the multi-agent system",
            "execution_history": []
        }
        
        print(f"📥 Input: {test_input['input']}\n")
        print("⚙️  Executing workflow with:")
        print("   ✓ Conditional routing (coordinator decides next agent)")
        print("   ✓ Retry loop (validator → processor if validation fails)")
        print("   ✓ Agent autonomy (confidence scores, routing decisions)")
        print("   ✓ Tool integration (dynamic tool selection)")
        print("   ✓ Execution history tracking")
        print("\n" + "=" * 70 + "\n")
        
        # Execute workflow
        result = graph.invoke(test_input)
        
        # Display workflow summary
        log_workflow_summary(result)
        
        # Display detailed results
        print("📊 Detailed Results:")
        print(f"\n🔀 Execution Path: {' → '.join(result.get('execution_history', []))}")
        print(f"\n📈 Agent Performance:")
        print(f"  - Coordinator: {result.get('coordinator_status', 'N/A')}")
        print(f"  - Processor: {result.get('processor_status', 'N/A')} (Confidence: {result.get('processor_confidence', 0):.2f})")
        print(f"  - Validator: {result.get('validator_status', 'N/A')} (Quality: {result.get('validation_score', 0):.2f})")
        
        # Show routing decisions
        print(f"\n🎯 Routing Decisions:")
        plan = result.get('plan', {})
        print(f"  - Coordinator decided: {result.get('next_agent', 'N/A')} (complexity: {plan.get('complexity', 0):.2f})")
        print(f"  - Retry count: {result.get('retry_count', 0)}")
        print(f"  - Final status: {result.get('workflow_status', 'N/A')}")
        
        # Show issues if any
        issues = result.get('validation_result', {}).get('issues', [])
        if issues:
            print(f"\n⚠️  Issues Detected: {', '.join(issues)}")
        else:
            print(f"\n✅ No issues detected")
        
        # Show final output
        print(f"\n📦 Final Output:")
        print(json.dumps(result.get('final_output', {}), indent=2))
        
        print("\n" + "=" * 70)
        print("🎯 Key Features Demonstrated:")
        print("  ✅ Dynamic routing (coordinator decides next agent)")
        print("  ✅ Retry loop (validator → processor on failure)")
        print("  ✅ Agent autonomy (confidence, quality scores, routing)")
        print("  ✅ Tool integration (agents use tools from registry)")
        print("  ✅ Structured state (type-safe schema)")
        print("  ✅ Observability (timestamped logs, execution history)")
        print("=" * 70)
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
