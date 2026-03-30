# LangGraph Multi-Agent System

Production-ready multi-agent AI system architecture built with LangGraph.

## Architecture Overview

This is a generic multi-agent system where specialized agents collaborate to complete tasks:

```
User Input → Coordinator Agent → Processor Agent → Validator Agent → Output
                    ↓                    ↓                  ↓
                  Plan              Process            Validate
```

## Project Structure

```
app/
├── agents/         # Specialized AI agents
│   ├── base_agent.py           # Abstract base class
│   ├── coordinator_agent.py    # Plans and orchestrates
│   ├── processor_agent.py      # Executes main logic
│   └── validator_agent.py      # Quality checks
│
├── tools/          # Reusable tools for agents
│   ├── base_tool.py            # Abstract base class
│   ├── data_transformer.py     # Data transformation
│   ├── validator_tool.py       # Validation utilities
│   └── tool_registry.py        # Tool management
│
├── graphs/         # LangGraph workflows
│   ├── multi_agent_graph.py    # Main workflow
│   ├── agent_registry.py       # Agent management
│   └── sample_graph.py         # Simple example
│
├── prompts/        # Prompt templates
│   ├── coordinator_prompt.txt
│   ├── processor_prompt.txt
│   └── validator_prompt.txt
│
├── config/         # Configuration
└── utils/          # Utilities

api/                # FastAPI application
tests/              # Comprehensive tests
```

## Core Concepts

### Dynamic Routing
The system uses conditional edges for intelligent routing:
- Validator can loop back to Processor if validation fails
- Coordinator analyzes complexity to determine workflow
- Agents make autonomous routing decisions

### Retry Loop
```
Coordinator → Processor → Validator
                  ↑           ↓
                  └───────────┘ (retry up to 3 times)
```

### Agents
Specialized AI components with autonomy:
- **Coordinator**: Analyzes requests, creates plans, determines complexity
- **Processor**: Executes logic, uses tools, provides confidence scores
- **Validator**: Quality checks, decides retry/approve, calculates scores

### Tools
Reusable utilities that agents dynamically select:
- **DataTransformer**: Format and transform data
- **ValidatorTool**: Run validation checks

Agents choose tools based on task requirements.

### Structured State
Type-safe state schema (`AgentState`) ensures:
- Clear data contracts between agents
- Type safety and IDE support
- Easier debugging and maintenance

### Registries
Centralized management:
- **AgentRegistry**: Discover and instantiate agents
- **ToolRegistry**: Access available tools

## Setup

1. Create virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Configure environment:
```bash
cp .env.example .env
# Edit .env with your API keys
```

4. Run multi-agent system:
```bash
python main.py
```

5. Run API server:
```bash
uvicorn api.main:app --reload --host 0.0.0.0 --port 8000
```

## Usage Examples

### Run Multi-Agent Workflow
```python
from app.graphs.multi_agent_graph import build_multi_agent_graph

graph = build_multi_agent_graph()
result = graph.invoke({"input": "Your task here"})
print(result["final_output"])
```

### Use Agent Registry
```python
from app.graphs.agent_registry import AgentRegistry

# List available agents
agents = AgentRegistry.list_agents()

# Get specific agent
coordinator = AgentRegistry.get_agent("coordinator")
```

### Use Tool Registry
```python
from app.tools.tool_registry import ToolRegistry

# List available tools
tools = ToolRegistry.list_tools()

# Use a tool
transformer = ToolRegistry.get_tool("data_transformer")
result = transformer.execute(data, transform_type="normalize")
```

## API Endpoints

- `GET /` - Health check
- `GET /health` - Detailed health status
- `POST /workflows/execute` - Execute workflow
- `GET /workflows/status` - Workflow system status

## Development

- Run tests: `pytest`
- Run tests with coverage: `pytest --cov=app`
- Format code: `black .`
- Lint: `ruff check .`
- Type check: `mypy app/`

## Extending the System

### Add New Agent
1. Create agent class inheriting from `BaseAgent`
2. Implement `execute()` method with routing logic
3. Register in `AgentRegistry`
4. Add routing conditions in graph

### Add New Tool
1. Create tool class inheriting from `BaseTool`
2. Implement `execute()` method
3. Register in `ToolRegistry`
4. Agents can now discover and use it

### Modify Routing
Edit routing functions in `app/graphs/multi_agent_graph.py`:
- `route_after_coordinator()` - Control flow after planning
- `route_after_validator()` - Control retry logic

## Key Features

✅ **Dynamic Routing** - Conditional edges, not fixed pipelines  
✅ **Retry Loop** - Automatic retry on validation failure  
✅ **Agent Autonomy** - Confidence scores, tool selection, routing decisions  
✅ **Tool Integration** - Agents dynamically use tools from registry  
✅ **Structured State** - Type-safe state schema (`AgentState`)  
✅ **Scalable** - Easy to add agents, tools, and routing logic  

See `ARCHITECTURE.md` for detailed design decisions.

## CI/CD

GitHub Actions pipeline includes:
- Multi-version Python testing (3.10, 3.11, 3.12)
- Code formatting (Black)
- Linting (Ruff)
- Type checking (MyPy)
- Security scanning (Safety, Bandit)
- Test coverage reporting
