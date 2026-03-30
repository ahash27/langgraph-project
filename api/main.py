"""FastAPI application for LangGraph workflows"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.config.settings import ENVIRONMENT
from api.routes.workflows import router as workflows_router

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
        "version": "1.0.0"
    }
