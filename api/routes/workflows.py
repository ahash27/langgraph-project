"""Workflow execution endpoints"""

from pathlib import Path

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from app.config import settings
from app.graphs.sample_graph import build_graph

router = APIRouter(prefix="/workflows", tags=["workflows"])

_REPO_ROOT = Path(__file__).resolve().parents[2]
_POST_GEN_CONFIG = _REPO_ROOT / "app" / "config" / "post_generation.json"


def build_sp01_readiness_payload() -> dict:
    """Sync body for GET /workflows/sp01-readiness (testable without TestClient)."""
    _has_openai = bool(settings.OPENAI_API_KEY and str(settings.OPENAI_API_KEY).strip())
    _has_or = bool(settings.OPENROUTER_API_KEY and str(settings.OPENROUTER_API_KEY).strip())
    graph_ok = False
    try:
        from app.graphs.multi_agent_graph import build_multi_agent_graph

        build_multi_agent_graph()
        graph_ok = True
    except Exception:
        graph_ok = False

    return {
        "post_generation_config_exists": _POST_GEN_CONFIG.is_file(),
        "llm_configured": _has_openai or _has_or,
        "linkedin_rate_limit": {
            "min_interval_seconds": settings.LINKEDIN_MIN_POST_INTERVAL_SECONDS,
            "max_posts_per_day": settings.LINKEDIN_MAX_POSTS_PER_DAY,
        },
        "multi_agent_graph_loads": graph_ok,
    }

class WorkflowRequest(BaseModel):
    input: str

class WorkflowResponse(BaseModel):
    message: str
    status: str

@router.post("/execute", response_model=WorkflowResponse)
async def execute_workflow(request: WorkflowRequest):
    """Execute a LangGraph workflow"""
    try:
        graph = build_graph()
        result = graph.invoke({"input": request.input})
        
        return WorkflowResponse(
            message=result.get("message", ""),
            status="success"
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/status")
async def workflow_status():
    """Get workflow system status"""
    return {
        "available_workflows": ["sample_graph", "multi_agent_graph"],
        "sp01": "post_generation_node",
        "status": "operational",
    }


@router.get("/sp01-readiness")
async def sp01_readiness():
    """SP-01 ops check: config on disk, LLM env, rate limits, graph compiles (no LLM call)."""
    return build_sp01_readiness_payload()
