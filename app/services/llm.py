"""Shared LLM utilities with OpenRouter primary and Gemini fallback."""

from __future__ import annotations

from typing import Any, Optional

import google.generativeai as genai
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


def _openai_key_set() -> bool:
    k = settings.OPENAI_API_KEY
    return bool(k and str(k).strip())


def _gemini_key_set() -> bool:
    k = settings.GEMINI_API_KEY
    return bool(k and str(k).strip())


def _provider_order() -> list[str]:
    raw = (settings.LLM_PROVIDER_ORDER or "openrouter,gemini").strip()
    allowed = {"openrouter", "gemini", "openai"}
    parsed = [p.strip().lower() for p in raw.split(",") if p.strip()]
    out: list[str] = []
    for p in parsed:
        if p in allowed and p not in out:
            out.append(p)
    if not out:
        return ["openrouter", "gemini"]
    if not settings.LLM_FALLBACK_ENABLED:
        return [out[0]]
    return out


def _build_openrouter_model(
    *,
    temperature: Optional[float] = None,
    max_tokens: Optional[int] = None,
    model: Optional[str] = None,
) -> ChatOpenAI:
    temp = settings.OPENAI_TEMPERATURE if temperature is None else temperature
    mx = settings.OPENAI_MAX_TOKENS if max_tokens is None else max_tokens
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


def _build_openai_model(
    *,
    temperature: Optional[float] = None,
    max_tokens: Optional[int] = None,
    model: Optional[str] = None,
) -> ChatOpenAI:
    temp = settings.OPENAI_TEMPERATURE if temperature is None else temperature
    mx = settings.OPENAI_MAX_TOKENS if max_tokens is None else max_tokens
    m = model or settings.OPENAI_MODEL
    return ChatOpenAI(
        model=m,
        api_key=settings.OPENAI_API_KEY,
        temperature=temp,
        max_tokens=mx,
    )


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
    if _openrouter_key_set():
        return _build_openrouter_model(
            temperature=temperature,
            max_tokens=max_tokens,
            model=model,
        )

    if not _openai_key_set():
        raise RuntimeError(
            "No LLM configured: set OPENROUTER_API_KEY or OPENAI_API_KEY in the environment."
        )

    return _build_openai_model(
        temperature=temperature,
        max_tokens=max_tokens,
        model=model,
    )


def llm_backend_label() -> str:
    order = _provider_order()
    return order[0] if order else ("openrouter" if _openrouter_key_set() else "openai")


def active_model_name() -> str:
    backend = llm_backend_label()
    if backend == "openrouter":
        return settings.OPENROUTER_MODEL
    if backend == "gemini":
        return settings.GEMINI_MODEL
    return settings.OPENAI_MODEL


def _invoke_gemini(messages: list[Any]) -> Any:
    genai.configure(api_key=settings.GEMINI_API_KEY)
    model = genai.GenerativeModel(settings.GEMINI_MODEL)
    prompt_parts: list[str] = []
    for msg in messages:
        content = getattr(msg, "content", msg)
        if isinstance(content, str):
            prompt_parts.append(content)
        elif isinstance(content, list):
            prompt_parts.extend(str(x) for x in content)
        else:
            prompt_parts.append(str(content))
    full_prompt = "\n\n".join(prompt_parts)
    resp = model.generate_content(full_prompt)
    text = getattr(resp, "text", None) or ""

    class _SimpleResp:
        def __init__(self, content: str) -> None:
            self.content = content

    return _SimpleResp(text)


def invoke_with_fallback(
    messages: list[Any],
    *,
    temperature: Optional[float] = None,
    max_tokens: Optional[int] = None,
    model: Optional[str] = None,
) -> tuple[Any, str]:
    errors: list[str] = []
    for provider in _provider_order():
        try:
            if provider == "openrouter" and _openrouter_key_set():
                resp = _build_openrouter_model(
                    temperature=temperature,
                    max_tokens=max_tokens,
                    model=model,
                ).invoke(messages)
                return resp, "openrouter"
            if provider == "openai" and _openai_key_set():
                resp = _build_openai_model(
                    temperature=temperature,
                    max_tokens=max_tokens,
                    model=model,
                ).invoke(messages)
                return resp, "openai"
            if provider == "gemini" and _gemini_key_set():
                resp = _invoke_gemini(messages)
                return resp, "gemini"
        except Exception as e:  # noqa: BLE001
            errors.append(f"{provider}: {e}")
            continue

    details = "; ".join(errors) if errors else "No provider keys configured."
    raise RuntimeError(f"All LLM providers failed: {details}")
