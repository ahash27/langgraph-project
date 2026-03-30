# LangGraph Social Media Automation

Production-ready AI workflow system built with LangGraph.

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

4. Run sample graph:
```bash
python main.py
```

## Project Structure

```
app/
├── graphs/     # LangGraph workflow definitions
├── nodes/      # Individual AI processing steps
├── services/   # External API integrations
├── utils/      # Helper functions
└── config/     # Configuration management

api/            # FastAPI routes (future)
tests/          # Unit tests
```

## Development

- Run tests: `pytest`
- Format code: `black .`
- Lint: `ruff check .`
