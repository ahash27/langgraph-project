"""FastAPI application for LangGraph workflows"""

import os

from dotenv import load_dotenv

load_dotenv()
if (
    os.getenv("LANGCHAIN_TRACING_V2", "false").lower() == "true"
    and not (os.getenv("LANGCHAIN_API_KEY") or os.getenv("LANGSMITH_API_KEY") or "").strip()
):
    os.environ["LANGCHAIN_TRACING_V2"] = "false"

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.config.settings import ENVIRONMENT
from app.services.llm import active_model_name, llm_backend_label
from app.database import init_db
from app.services.scheduler import get_scheduler
from api.routes.auth import router as auth_router
from api.routes.demo import router as demo_router
from api.routes.linkedin import router as linkedin_router
from api.routes.workflows import router as workflows_router
from api.routes.scheduled_posts import router as scheduled_posts_router

app = FastAPI(
    title="LangGraph API",
    description="API for AI workflow automation",
    version="1.0.0"
)

# Initialize database
init_db()

# Initialize scheduler
get_scheduler()

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(workflows_router)
app.include_router(auth_router)
app.include_router(linkedin_router)
app.include_router(demo_router)
app.include_router(scheduled_posts_router)

@app.get("/")
async def root():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "environment": ENVIRONMENT,
        "service": "LangGraph API"
    }

@app.get("/health")
async def health():
    """Detailed health check"""
    return {
        "status": "ok",
        "version": "1.0.0",
        "llm_backend": llm_backend_label(),
        "llm_model": active_model_name(),
    }
