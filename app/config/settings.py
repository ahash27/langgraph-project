import os
from dotenv import load_dotenv

load_dotenv()

# OpenAI Configuration
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
OPENAI_MODEL = os.getenv("OPENAI_MODEL", "gpt-4o-mini")
OPENAI_TEMPERATURE = float(os.getenv("OPENAI_TEMPERATURE", "0.7"))
OPENAI_MAX_TOKENS = int(os.getenv("OPENAI_MAX_TOKENS", "2000"))

# OpenRouter (OpenAI-compatible base URL + key)
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")
OPENROUTER_BASE_URL = os.getenv("OPENROUTER_BASE_URL", "https://openrouter.ai/api/v1")
OPENROUTER_MODEL = os.getenv("OPENROUTER_MODEL", "openrouter/free")
OPENROUTER_HTTP_REFERER = os.getenv("OPENROUTER_HTTP_REFERER", "http://localhost:8000")
OPENROUTER_APP_TITLE = os.getenv("OPENROUTER_APP_TITLE", "langgraph-project")

# Gemini direct fallback (Google AI Studio)
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
GEMINI_MODEL = os.getenv("GEMINI_MODEL", "gemini-1.5-flash")
LLM_FALLBACK_ENABLED = os.getenv("LLM_FALLBACK_ENABLED", "true").lower() == "true"
LLM_PROVIDER_ORDER = os.getenv("LLM_PROVIDER_ORDER", "openrouter,gemini")

# LangSmith Tracing
LANGCHAIN_API_KEY = os.getenv("LANGCHAIN_API_KEY")
LANGCHAIN_TRACING_V2 = os.getenv("LANGCHAIN_TRACING_V2", "false").lower() == "true"
LANGCHAIN_PROJECT = os.getenv("LANGCHAIN_PROJECT", "langgraph-project")

# Application Settings
ENVIRONMENT = os.getenv("ENVIRONMENT", "development")
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
DEBUG = os.getenv("DEBUG", "false").lower() == "true"

# API Configuration
API_HOST = os.getenv("API_HOST", "0.0.0.0")
API_PORT = int(os.getenv("API_PORT", "8000"))
API_RELOAD = os.getenv("API_RELOAD", "true").lower() == "true"

# Social Media APIs (Future)
TWITTER_API_KEY = os.getenv("TWITTER_API_KEY")
TWITTER_API_SECRET = os.getenv("TWITTER_API_SECRET")
LINKEDIN_CLIENT_ID = os.getenv("LINKEDIN_CLIENT_ID")
LINKEDIN_CLIENT_SECRET = os.getenv("LINKEDIN_CLIENT_SECRET")

# LinkedIn publish throttling (Phase 4; use with UGC/post APIs only)
LINKEDIN_MIN_POST_INTERVAL_SECONDS = int(os.getenv("LINKEDIN_MIN_POST_INTERVAL_SECONDS", "120"))
LINKEDIN_MAX_POSTS_PER_DAY = int(os.getenv("LINKEDIN_MAX_POSTS_PER_DAY", "50"))

# Database
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./langgraph.db")

# Redis Cache
REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379/0")

# Rate Limiting
RATE_LIMIT_PER_MINUTE = int(os.getenv("RATE_LIMIT_PER_MINUTE", "60"))

def validate_config():
    """Validate required configuration"""
    _has_openai = bool(OPENAI_API_KEY and str(OPENAI_API_KEY).strip())
    _has_or = bool(OPENROUTER_API_KEY and str(OPENROUTER_API_KEY).strip())
    if not _has_openai and not _has_or:
        raise ValueError("Set OPENROUTER_API_KEY or OPENAI_API_KEY")
    
    if ENVIRONMENT not in ["development", "staging", "production"]:
        raise ValueError(f"Invalid ENVIRONMENT: {ENVIRONMENT}")
