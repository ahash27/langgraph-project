"""LangGraph node: generate three LinkedIn variants (SP-01).

Draft-only here. When you add publishing, wrap the LinkedIn HTTP call with
``app.services.linkedin_rate_limit.get_linkedin_write_rate_limiter().run_throttled(...)``.
"""

from __future__ import annotations

from typing import List

from app.graphs.state_schema import AgentState, TrendItem, TrendsData
from app.services.generate_posts import generate_posts_bundle
from app.utils.logger import log_agent_step


def _related_queries_as_string(trend: TrendItem) -> str:
    rq = trend.get("related_queries") or []
    if isinstance(rq, list):
        return ", ".join(str(x) for x in rq if x)
    return str(rq)


def _trend_context(state: AgentState) -> tuple[str, str, str]:
    """topic, description, related_queries string."""
    processed = state.get("processed_output") or {}
    trends_data: TrendsData = processed.get("trends_data") or {}
    trends: List[TrendItem] = trends_data.get("trends") or []

    if trends:
        t0 = trends[0]
        topic = (t0.get("topic") or t0.get("description") or "").strip() or "trend"
        desc = (t0.get("description") or "").strip()
        rq = _related_queries_as_string(t0)
        return topic, desc, rq

    plan = state.get("plan") or {}
    topic = (plan.get("task") or state.get("input") or "").strip() or "topic"
    return topic, "", ""


def generate_posts(state: AgentState) -> AgentState:
    log_agent_step("generate_posts", state, "start")
    topic, description, related_queries = _trend_context(state)
    execution_history = [*state.get("execution_history", []), "generate_posts"]

    try:
        bundle = generate_posts_bundle(
            topic=topic,
            description=description,
            related_queries=related_queries,
        )
        log_agent_step("generate_posts", {"topic": topic}, "complete")
        return {
            **state,
            "generated_posts": bundle.model_dump(),
            "generate_posts_status": "completed",
            "generate_posts_error": None,
            "execution_history": execution_history,
            "current_agent": "generate_posts",
        }
    except Exception as e:
        log_agent_step("generate_posts", {"error": str(e)}, "failed")
        return {
            **state,
            "generated_posts": {},
            "generate_posts_status": "failed",
            "generate_posts_error": str(e),
            "execution_history": execution_history,
            "current_agent": "generate_posts",
        }
