# Multi-Agent System Architecture

## Overview

This is a production-ready multi-agent system with dynamic routing, retry loops, and agent autonomy.

## Key Features

### 1. Dynamic Routing (Conditional Edges)
Agents don't follow a fixed pipeline - they make routing decisions:

```python
# Validator can route back to Processor for retry
def route_after_validator(state):
    if not state["is_valid"] and state["retry_count"] < max_retries:
        return "processor"  # Retry loop
    return "end"
```

### 2. Retry Loop
If validation fails, the system automatically retries:
```
Coordinator → Processor → Validator
                  ↑           ↓
                  └───────────┘ (retry if validation fails)
```

### 3. Agent Autonomy
Agents make decisions and provide metadata:
- Confidence scores
- Routing suggestions
- Tool selection
- Quality assessments

### 4. Tool Integration
Agents dynamically select and use tools from registry:
```python
if "data_transformer" in plan["requires_tools"]:
    result = self.tools["data_transformer"].execute(data)
```

### 5. Structured State
Type-safe state schema ensures data contracts:
```python
class AgentState(TypedDict):
    input: str
    plan: Dict[str, Any]
    processed_output: Dict[str, Any]
    is_valid: bool
    retry_count: int
```

## Architecture Decisions

### Why Conditional Routing?
- Enables true multi-agent behavior
- Agents can adapt to different scenarios
- System can handle failures gracefully

### Why Retry Loop?
- Improves reliability
- Allows self-correction
- Prevents single-point failures

### Why Tool Registry?
- Plug-and-play architecture
- Easy to add new capabilities
- Agents discover tools dynamically

### Why Structured State?
- Type safety
- Clear data contracts
- Easier debugging
- Better IDE support

## Extending the System

### Add New Agent
1. Inherit from `BaseAgent`
2. Implement `execute()` method
3. Register in `AgentRegistry`
4. Add routing logic in graph

### Add New Tool
1. Inherit from `BaseTool`
2. Implement `execute()` method
3. Register in `ToolRegistry`

### Modify Routing
Edit routing functions in `multi_agent_graph.py`
