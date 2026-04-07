"""FastAPI application for LangGraph workflows"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.config.settings import ENVIRONMENT
from app.services.llm import active_model_name, llm_backend_label
from api.routes.auth import router as auth_router
from api.routes.linkedin import router as linkedin_router
from api.routes.workflows import router as workflows_router
from api.routes.auth import router as auth_router

app = FastAPI(
    title="LangGraph API",
    description="API for AI workflow automation",
    version="1.0.0"
)

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
