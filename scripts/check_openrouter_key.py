"""Smoke-test OpenRouter from .env (run: py scripts/check_openrouter_key.py)."""

from pathlib import Path

from dotenv import load_dotenv
from openai import OpenAI
import os
import sys

_repo = Path(__file__).resolve().parents[1]
_env_path = _repo / ".env"
load_dotenv(_env_path)
key = os.getenv("OPENROUTER_API_KEY")
if not key:
    print("OPENROUTER_API_KEY is missing or empty.")
    print(f"Checked: {_env_path}")
    sys.exit(1)

base = os.getenv("OPENROUTER_BASE_URL", "https://openrouter.ai/api/v1").rstrip("/")
model = os.getenv("OPENROUTER_MODEL", "openrouter/free")

# OpenRouter recommends these headers (optional but helps routing / abuse checks).
_headers = {
    "HTTP-Referer": os.getenv("OPENROUTER_HTTP_REFERER", "http://localhost:8000"),
    "X-Title": os.getenv("OPENROUTER_APP_TITLE", "langgraph-project"),
}

client = OpenAI(api_key=key, base_url=base, default_headers=_headers)
r = client.chat.completions.create(
    model=model,
    messages=[{"role": "user", "content": "Reply with exactly: ok"}],
    max_tokens=32,
)
ch = r.choices[0]
msg = ch.message
print("model:", getattr(r, "model", "?"))
print("finish_reason:", ch.finish_reason)
text = msg.content
if text is None and getattr(msg, "refusal", None):
    print("refusal:", msg.refusal)
if text is None or (isinstance(text, str) and not text.strip()):
    print(
        "content: (empty) — key and API look fine; "
        "try OPENROUTER_MODEL set to a specific free model slug from openrouter.ai/models "
        "instead of openrouter/free."
    )
    sys.exit(1)
print("content:", text)
