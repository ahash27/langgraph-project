"""Workflow execution endpoints"""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from app.graphs.sample_graph import build_graph

router = APIRouter(prefix="/workflows", tags=["workflows"])

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
        "available_workflows": ["sample_graph"],
        "status": "operational"
    }
