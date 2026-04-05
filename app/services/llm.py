"""Shared LangChain chat model: OpenRouter when configured, else OpenAI."""

from __future__ import annotations

from typing import Optional

from langchain_openai import ChatOpenAI

from app.config import settings


def _openrouter_headers() -> dict[str, str]:
    return {
        "HTTP-Referer": settings.OPENROUTER_HTTP_REFERER,
        "X-Title": settings.OPENROUTER_APP_TITLE,
    }


def _openrouter_key_set() -> bool:
    k = settings.OPENROUTER_API_KEY
    return bool(k and str(k).strip())


def get_chat_model(
    *,
    temperature: Optional[float] = None,
    max_tokens: Optional[int] = None,
    model: Optional[str] = None,
) -> ChatOpenAI:
    """
    Return a ChatOpenAI instance. Uses OpenRouter if OPENROUTER_API_KEY is set;
    otherwise OpenAI (requires OPENAI_API_KEY).
    """
    temp = settings.OPENAI_TEMPERATURE if temperature is None else temperature
    mx = settings.OPENAI_MAX_TOKENS if max_tokens is None else max_tokens

    if _openrouter_key_set():
        m = model or settings.OPENROUTER_MODEL
        base = (settings.OPENROUTER_BASE_URL or "https://openrouter.ai/api/v1").rstrip("/")
        return ChatOpenAI(
            model=m,
            api_key=settings.OPENROUTER_API_KEY,
            base_url=base,
            temperature=temp,
            max_tokens=mx,
            default_headers=_openrouter_headers(),
        )

    if not settings.OPENAI_API_KEY or not str(settings.OPENAI_API_KEY).strip():
        raise RuntimeError(
            "No LLM configured: set OPENROUTER_API_KEY or OPENAI_API_KEY in the environment."
        )

    m = model or settings.OPENAI_MODEL
    return ChatOpenAI(
        model=m,
        api_key=settings.OPENAI_API_KEY,
        temperature=temp,
        max_tokens=mx,
    )


def llm_backend_label() -> str:
    return "openrouter" if _openrouter_key_set() else "openai"


def active_model_name() -> str:
    return settings.OPENROUTER_MODEL if _openrouter_key_set() else settings.OPENAI_MODEL
