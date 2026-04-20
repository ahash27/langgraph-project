"""Shared pytest fixtures."""

import os

# Avoid LangSmith 401 noise when LANGCHAIN_API_KEY is unset (tests still pass either way).
os.environ.setdefault("LANGCHAIN_TRACING_V2", "false")

import pytest

from app.schemas.post_generation import (
    MIN_POST_BODY_CHARS,
    GeneratedPostsBundle,
    LinkedInPostVariant,
)


def _fake_posts_bundle() -> GeneratedPostsBundle:
    chunk = "Test paragraph content. "
    body = (chunk * 30)[:MIN_POST_BODY_CHARS]
    return GeneratedPostsBundle(
        thought_leadership=LinkedInPostVariant(body=body, hashtags=["one", "two", "three"]),
        question_hook=LinkedInPostVariant(body=body, hashtags=["a", "b", "c", "d"]),
        data_insight=LinkedInPostVariant(body=body, hashtags=["x", "y", "z", "w", "q"]),
    )


@pytest.fixture(autouse=True)
def mock_generate_posts_llm(monkeypatch: pytest.MonkeyPatch) -> None:
    """Avoid real LLM calls during graph/agent tests."""
    monkeypatch.setattr(
        "app.nodes.generate_posts_node.generate_posts_bundle",
        lambda **kwargs: _fake_posts_bundle(),
    )
