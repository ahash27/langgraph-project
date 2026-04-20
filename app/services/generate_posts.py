"""Phase 2: call LLM and validate GeneratedPostsBundle (SP-01)."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, List

from langchain_core.messages import AIMessage, HumanMessage, SystemMessage
from pydantic import ValidationError

from app.config import settings
from app.schemas.post_generation import (
    MAX_POST_BODY_CHARS,
    MIN_POST_BODY_CHARS,
    GeneratedPostsBundle,
    load_post_generation_prompt_config,
)
from app.services.llm import invoke_with_fallback

# Completion budget for three long posts + JSON overhead
_DEFAULT_MAX_OUTPUT_TOKENS = 4096


def _flatten_message_content(content: Any) -> str:
    if isinstance(content, str):
        return content
    if isinstance(content, list):
        parts: List[str] = []
        for block in content:
            if isinstance(block, str):
                parts.append(block)
            elif isinstance(block, dict):
                t = block.get("text")
                if isinstance(t, str):
                    parts.append(t)
        return "".join(parts)
    return str(content)


def _strip_markdown_json_fence(text: str) -> str:
    if "```" not in text:
        return text.strip()
    first = text.find("```")
    rest = text[first + 3 :]
    if rest.lstrip().lower().startswith("json"):
        rest = rest.lstrip()[4:].lstrip()
        if rest.startswith("\n"):
            rest = rest[1:]
    last = rest.rfind("```")
    if last != -1:
        rest = rest[:last]
    return rest.strip()


def _extract_json_object(text: str) -> Any:
    """Parse JSON object from model output; tolerate fences and leading prose."""
    stripped = _strip_markdown_json_fence(text.strip())
    try:
        return json.loads(stripped)
    except json.JSONDecodeError:
        pass
    start = stripped.find("{")
    if start == -1:
        raise ValueError("No JSON object found in model output.") from None
    depth = 0
    for i in range(start, len(stripped)):
        c = stripped[i]
        if c == "{":
            depth += 1
        elif c == "}":
            depth -= 1
            if depth == 0:
                return json.loads(stripped[start : i + 1])
    raise ValueError("Unbalanced braces in JSON object.") from None


def _retry_instruction(error: BaseException) -> str:
    return (
        "Your previous reply was not usable. "
        f"Problem: {error!s}\n"
        "Reply with ONLY one JSON object (no markdown, no commentary) with keys: "
        "thought_leadership, question_hook, data_insight. "
        "Each value must be {\"body\": string, \"hashtags\": array of 3-5 strings}. "
        "Hashtags: single tokens, letters/digits/underscore only, no # in values. "
        f"Each body: at least {MIN_POST_BODY_CHARS}, at most {MAX_POST_BODY_CHARS} characters; "
        "aim for roughly 500-1200 when possible."
    )


def generate_posts_bundle(
    *,
    topic: str,
    description: str = "",
    related_queries: str = "",
    user_request: str = "",
    config_path: Path | None = None,
    model: Any | None = None,
    max_retries: int = 2,
    max_output_tokens: int | None = None,
) -> GeneratedPostsBundle:
    """
    Load prompts from config, invoke LLM, parse JSON, validate with Pydantic.
    On validation/parse failure, retries once with a repair instruction (default).
    """
    cfg = load_post_generation_prompt_config(config_path)
    mt = max_output_tokens or max(_DEFAULT_MAX_OUTPUT_TOKENS, settings.OPENAI_MAX_TOKENS)
    llm = model

    user_content = cfg.render_user_prompt(
        topic=topic or "",
        description=description or "",
        related_queries=related_queries or "",
        user_request=user_request or topic or "",
    )
    messages: List[Any] = [
        SystemMessage(content=cfg.brand_voice_system),
        HumanMessage(content=user_content),
    ]

    last_error: BaseException | None = None
    provider_used = "custom_model" if llm is not None else "auto"
    for attempt in range(max_retries + 1):
        if llm is not None:
            response = llm.invoke(messages)
        else:
            response, provider_used = invoke_with_fallback(
                messages,
                max_tokens=mt,
            )
        raw = _flatten_message_content(response.content)

        try:
            data = _extract_json_object(raw)
            return GeneratedPostsBundle.model_validate(data)
        except (json.JSONDecodeError, ValidationError, ValueError, TypeError) as e:
            last_error = e
            if attempt >= max_retries:
                break
            messages.append(AIMessage(content=raw))
            messages.append(HumanMessage(content=_retry_instruction(e)))

    raise RuntimeError(
        f"Failed to generate valid posts after {max_retries + 1} attempt(s). Provider: {provider_used}."
    ) from last_error
