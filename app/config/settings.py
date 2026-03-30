import os
from dotenv import load_dotenv

load_dotenv()

# API Keys
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
LANGCHAIN_API_KEY = os.getenv("LANGCHAIN_API_KEY")

# LangSmith Tracing
LANGCHAIN_TRACING_V2 = os.getenv("LANGCHAIN_TRACING_V2", "false").lower() == "true"

# Application
ENVIRONMENT = os.getenv("ENVIRONMENT", "development")

def validate_config():
    """Validate required configuration"""
    if not OPENAI_API_KEY:
        raise ValueError("OPENAI_API_KEY is required")
