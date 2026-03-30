# LangGraph Project

Scaffold for an AI workflow system built with LangGraph.

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

5. Run API server:
```bash
uvicorn api.main:app --reload --host 0.0.0.0 --port 8000
```

## Project Structure

```
app/
├── graphs/     # LangGraph workflow definitions
├── nodes/      # Individual AI processing steps
├── services/   # External API integrations
├── utils/      # Helper functions
└── config/     # Configuration management

api/            # FastAPI application
├── main.py     # FastAPI app entry
└── routes/     # API endpoints

tests/          # Unit tests
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

## CI/CD

GitHub Actions pipeline includes:
- Multi-version Python testing (3.10, 3.11, 3.12)
- Code formatting (Black)
- Linting (Ruff)
- Type checking (MyPy)
- Security scanning (Safety, Bandit)
- Test coverage reporting
