"""Smoke-test OPENAI_API_KEY from .env (run: py scripts/check_openai_key.py)."""

from pathlib import Path

from dotenv import load_dotenv
from openai import OpenAI
import os
import sys

_repo = Path(__file__).resolve().parents[1]
_env_path = _repo / ".env"
load_dotenv(_env_path)
key = os.getenv("OPENAI_API_KEY")
if not key:
    print("OPENAI_API_KEY is missing or empty after load_dotenv().")
    print(f"Checked: {_env_path}")
    print("Fix: put the key on the same line as OPENAI_API_KEY=... and Save the file (Ctrl+S).")
    sys.exit(1)

model = os.getenv("OPENAI_MODEL", "gpt-4o-mini")
client = OpenAI(api_key=key)
r = client.chat.completions.create(
    model=model,
    messages=[{"role": "user", "content": "Reply with exactly: ok"}],
    max_tokens=10,
)
print(r.choices[0].message.content)
