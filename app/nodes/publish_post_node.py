"""LangGraph node: publish approved copy to LinkedIn; stores post URN; idempotent."""

from __future__ import annotations

import hashlib
from typing import Any, cast

from app.graphs.state_schema import AgentState
from app.services.linkedin_publish import publish_text_share
from app.utils.logger import log_agent_step


def _fingerprint(text: str) -> str:
    return hashlib.sha256(text.strip().encode("utf-8")).hexdigest()


def publish_post(state: AgentState) -> AgentState:
    log_agent_step("publish_post", cast(AgentState, state), "start")
    hist = [*state.get("execution_history", []), "publish_post"]
    out: dict[str, Any] = {
        "execution_history": hist,
        "current_agent": "publish_post",
    }

    if not state.get("approved_for_publish"):
        out["publish_post_status"] = "skipped_not_approved"
        out["publish_post_error"] = None
        return cast(AgentState, out)

    text = (state.get("publish_draft_text") or "").strip()
    if not text:
        out["publish_post_status"] = "skipped_no_draft"
        out["publish_post_error"] = None
        return cast(AgentState, out)

    fp = _fingerprint(text)
    if state.get("linkedin_publish_fingerprint") == fp and state.get("linkedin_post_urn"):
        out["publish_post_status"] = "skipped_idempotent"
        out["publish_post_error"] = None
        return cast(AgentState, out)

    try:
        result = publish_text_share(text)
        urn = result.get("id")
        if not urn:
            out["publish_post_status"] = "failed"
            out["publish_post_error"] = "LinkedIn response missing id"
            return cast(AgentState, out)
        out["linkedin_post_urn"] = str(urn)
        out["linkedin_publish_fingerprint"] = fp
        out["publish_post_status"] = "completed"
        out["publish_post_error"] = None
        log_agent_step("publish_post", cast(AgentState, {**state, **out}), "complete")
    except Exception as e:
        out["publish_post_status"] = "failed"
        out["publish_post_error"] = str(e)
        log_agent_step("publish_post", cast(AgentState, {**state, **out}), "failed")

    return cast(AgentState, out)
