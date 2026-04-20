"""LangGraph node: generate three LinkedIn variants (SP-01).

Draft-only here. When you add publishing, wrap the LinkedIn HTTP call with
``app.services.linkedin_rate_limit.get_linkedin_write_rate_limiter().run_throttled(...)``.
"""

from __future__ import annotations

import re
from typing import List, Tuple

from app.graphs.state_schema import AgentState, TrendItem, TrendsData
from app.services.generate_posts import generate_posts_bundle
from app.utils.logger import log_agent_step

_STOPWORDS = frozenset(
    """
    the a an and or for to of in on at with is are was were be been being
    this that these those it its we you they he she i my your their our
    what which who how when where why write writing post linkedin about
    trending trend trends current now week professional tone use using
    create creating draft three one two give me please just
    """.split()
)


def _tokens(s: str) -> set[str]:
    return {
        t
        for t in re.findall(r"[a-z0-9]+", (s or "").lower())
        if len(t) > 2 and t not in _STOPWORDS
    }


def _trend_blob(t: TrendItem) -> str:
    parts = [
        str(t.get("topic") or ""),
        str(t.get("description") or ""),
        _related_queries_as_string(t),
    ]
    return " ".join(parts)


def _related_queries_as_string(trend: TrendItem) -> str:
    rq = trend.get("related_queries") or []
    if isinstance(rq, list):
        return ", ".join(str(x) for x in rq if x)
    return str(rq)


def _best_trend_for_user(user_request: str, trends: List[TrendItem]) -> Tuple[TrendItem | None, int]:
    u = _tokens(user_request)
    if not u or not trends:
        return (trends[0] if trends else None, 0)
    best: TrendItem | None = None
    best_score = -1
    for t in trends:
        blob = _trend_blob(t)
        score = len(u & _tokens(blob))
        if score > best_score:
            best_score = score
            best = t
    return (best, best_score)


def _trend_context(state: AgentState) -> tuple[str, str, str, str, dict[str, object]]:
    """topic, description, related_queries, user_request, debug context."""
    plan = state.get("plan") or {}
    user_request = (state.get("input") or plan.get("task") or "").strip() or "general professional topic"

    processed = state.get("processed_output") or {}
    trends_data: TrendsData = processed.get("trends_data") or {}
    trends: List[TrendItem] = list(trends_data.get("trends") or [])
    if not trends:
        top = state.get("trends")
        if isinstance(top, list):
            trends = [t for t in top if isinstance(t, dict)]

    if not trends:
        ctx = {
            "user_request": user_request,
            "trend_match_score": 0,
            "trend_topic_picked": None,
            "region": state.get("region"),
        }
        return user_request, "", "", user_request, ctx

    best, score = _best_trend_for_user(user_request, trends)
    if best is None:
        best = trends[0]
        score = 0

    t_topic = (best.get("topic") or "").strip()
    t_desc = (best.get("description") or "").strip()
    rq = _related_queries_as_string(best)

    tops_preview = "; ".join(
        (t.get("topic") or "") for t in trends[:5] if t.get("topic")
    )

    if score > 0:
        description = (
            f"Best-matching US/regional trend row for the user keywords (score {score}): "
            f"“{t_topic}”. " + (f"Detail: {t_desc}" if t_desc else "")
        ).strip()
    else:
        description = (
            "Low keyword overlap between the user request and merged trend titles; "
            "still honor the user request. "
            f"Light US trend snapshot only: {tops_preview}"
        )
        rq = rq or tops_preview

    topic = user_request
    ctx = {
        "user_request": user_request,
        "trend_topic_picked": t_topic or None,
        "trend_match_score": score,
        "trends_preview": tops_preview,
        "region": state.get("region"),
    }
    return topic, description, rq, user_request, ctx


def generate_posts(state: AgentState) -> AgentState:
    log_agent_step("generate_posts", state, "start")
    topic, description, related_queries, user_request, gp_context = _trend_context(state)
    execution_history = [*state.get("execution_history", []), "generate_posts"]

    try:
        bundle = generate_posts_bundle(
            topic=topic,
            description=description,
            related_queries=related_queries,
            user_request=user_request,
        )
        log_agent_step("generate_posts", {"topic": topic}, "complete")
        return {
            **state,
            "generated_posts": bundle.model_dump(),
            "generate_posts_status": "completed",
            "generate_posts_error": None,
            "generate_posts_context": gp_context,
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
            "generate_posts_context": gp_context,
            "execution_history": execution_history,
            "current_agent": "generate_posts",
        }
