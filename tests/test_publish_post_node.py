"""Tests for publish_post LangGraph node (LinkedIn delivery, idempotency)."""

from unittest.mock import patch

from app.graphs.multi_agent_graph import route_after_validator
from app.nodes.publish_post_node import publish_post


def test_route_after_validator_publish_when_approved():
    state = {
        "is_valid": True,
        "retry_count": 0,
        "max_retries": 3,
        "approved_for_publish": True,
        "publish_draft_text": "Hello #a #b #c",
    }
    assert route_after_validator(state) == "publish_post"


def test_route_after_validator_end_when_valid_but_not_approved():
    state = {
        "is_valid": True,
        "retry_count": 0,
        "max_retries": 3,
        "approved_for_publish": False,
        "publish_draft_text": "x",
    }
    assert route_after_validator(state) == "end"


def test_publish_post_skipped_not_approved():
    out = publish_post({"execution_history": [], "approved_for_publish": False})
    assert out["publish_post_status"] == "skipped_not_approved"


def test_publish_post_skipped_no_draft():
    out = publish_post(
        {"execution_history": [], "approved_for_publish": True, "publish_draft_text": "   "}
    )
    assert out["publish_post_status"] == "skipped_no_draft"


def test_publish_post_idempotent():
    out = publish_post(
        {
            "execution_history": [],
            "approved_for_publish": True,
            "publish_draft_text": "Same text",
            "linkedin_post_urn": "urn:li:share:1",
            "linkedin_publish_fingerprint": __import__(
                "hashlib"
            ).sha256("Same text".encode("utf-8")).hexdigest(),
        }
    )
    assert out["publish_post_status"] == "skipped_idempotent"


def test_publish_post_completes_and_sets_urn():
    with patch(
        "app.nodes.publish_post_node.publish_text_share",
        return_value={"id": "urn:li:share:99"},
    ):
        out = publish_post(
            {
                "execution_history": [],
                "approved_for_publish": True,
                "publish_draft_text": "Post me\n#x #y #z",
            }
        )
    assert out["publish_post_status"] == "completed"
    assert out["linkedin_post_urn"] == "urn:li:share:99"
    assert out["linkedin_publish_fingerprint"]
    assert out["execution_history"][-1] == "publish_post"


def test_publish_post_failed_on_linkedin_error():
    with patch(
        "app.nodes.publish_post_node.publish_text_share",
        side_effect=RuntimeError("token missing"),
    ):
        out = publish_post(
            {
                "execution_history": [],
                "approved_for_publish": True,
                "publish_draft_text": "x",
            }
        )
    assert out["publish_post_status"] == "failed"
    assert "token missing" in (out.get("publish_post_error") or "")
