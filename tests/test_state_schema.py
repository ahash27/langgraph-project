"""Tests for the shared LangGraph state schema."""

from typing import Annotated, List, get_args, get_origin, get_type_hints

from app.graphs.state_schema import AgentState, merge_lists


def test_merge_lists_appends_items():
    """List reducer should append new items instead of overwriting."""
    existing = [{"name": "AI"}]
    incoming = [{"name": "Robotics"}]

    result = merge_lists(existing, incoming)

    assert result == [{"name": "AI"}, {"name": "Robotics"}]


def test_agent_state_includes_social_media_fields():
    """Schema should expose the shared social-media workflow fields."""
    hints = get_type_hints(AgentState, include_extras=True)

    for field in (
        "schema_version",
        "trends",
        "selected_trend",
        "post_drafts",
        "approved_post",
        "engagement_metrics",
    ):
        assert field in hints


def test_list_fields_use_reducers():
    """List-based fields should define merge behavior for LangGraph."""
    hints = get_type_hints(AgentState, include_extras=True)

    trends_hint = hints["trends"]
    post_drafts_hint = hints["post_drafts"]
    engagement_metrics_hint = hints["engagement_metrics"]

    assert get_origin(trends_hint) is Annotated
    assert get_origin(post_drafts_hint) is Annotated
    assert get_origin(engagement_metrics_hint) is Annotated

    assert get_args(trends_hint)[1] is merge_lists
    assert get_args(post_drafts_hint)[1] is merge_lists
    assert get_args(engagement_metrics_hint)[1] is merge_lists
