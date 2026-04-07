"""Phase 5: SP-01 node tests + readiness API (no live LLM)."""

from pathlib import Path

import pytest

pytestmark = pytest.mark.sp01
from api.routes.workflows import build_sp01_readiness_payload

from app.nodes.generate_posts_node import _trend_context, generate_posts
from app.schemas.post_generation import GeneratedPostsBundle, LinkedInPostVariant


def _stub_bundle() -> GeneratedPostsBundle:
    v = LinkedInPostVariant(body="b", hashtags=["a", "b", "c"])
    return GeneratedPostsBundle(
        thought_leadership=v,
        question_hook=LinkedInPostVariant(body="q", hashtags=["a", "b", "c", "d"]),
        data_insight=LinkedInPostVariant(body="d", hashtags=["a", "b", "c", "d", "e"]),
    )


def test_trend_context_from_first_trend():
    state = {
        "processed_output": {
            "trends_data": {
                "trends": [
                    {
                        "topic": "AI",
                        "description": "ML boom",
                        "related_queries": ["gpt", "llm"],
                    }
                ]
            }
        }
    }
    topic, desc, rq = _trend_context(state)
    assert topic == "AI"
    assert desc == "ML boom"
    assert "gpt" in rq and "llm" in rq


def test_trend_context_fallback_to_plan_and_input():
    state = {"plan": {"task": "My task"}, "input": "ignored if plan task set"}
    assert _trend_context(state) == ("My task", "", "")
    state2 = {"input": "Only input"}
    assert _trend_context(state2)[0] == "Only input"


def test_trend_context_empty_defaults_topic():
    state: dict = {}
    assert _trend_context(state) == ("topic", "", "")


def test_generate_posts_node_success(monkeypatch: pytest.MonkeyPatch):
    monkeypatch.setattr(
        "app.nodes.generate_posts_node.generate_posts_bundle",
        lambda **kw: _stub_bundle(),
    )
    out = generate_posts({"execution_history": ["processor"]})
    assert out["generate_posts_status"] == "completed"
    assert out["generated_posts"]["thought_leadership"]["body"] == "b"
    assert out["execution_history"][-1] == "generate_posts"


def test_generate_posts_node_failure(monkeypatch: pytest.MonkeyPatch):
    def boom(**kwargs):
        raise RuntimeError("llm unavailable")

    monkeypatch.setattr("app.nodes.generate_posts_node.generate_posts_bundle", boom)
    out = generate_posts({"execution_history": []})
    assert out["generate_posts_status"] == "failed"
    assert "llm unavailable" in (out.get("generate_posts_error") or "")


def test_sp01_readiness_payload():
    data = build_sp01_readiness_payload()
    assert data["post_generation_config_exists"] is True
    assert "llm_configured" in data
    assert data["linkedin_rate_limit"]["min_interval_seconds"] >= 0
    assert data["multi_agent_graph_loads"] is True


def test_post_generation_config_path_resolution():
    """Sanity: default JSON path matches repo layout."""
    root = Path(__file__).resolve().parents[1]
    p = root / "app" / "config" / "post_generation.json"
    assert p.is_file()
