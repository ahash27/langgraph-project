"""Unit tests for LinkedIn publish (mocked HTTP)."""

from unittest.mock import MagicMock, patch

import pytest

from app.schemas.post_generation import (
    MIN_POST_BODY_CHARS,
    GeneratedPostsBundle,
    LinkedInPostVariant,
)
from app.services.linkedin_publish import publish_generated_variant, publish_text_share


@pytest.fixture
def fake_limiter(monkeypatch: pytest.MonkeyPatch):
    class _L:
        def run_throttled(self, fn):
            return fn()

    monkeypatch.setattr(
        "app.services.linkedin_publish.get_linkedin_write_rate_limiter",
        lambda: _L(),
    )


@pytest.fixture
def fake_token_and_urn(monkeypatch: pytest.MonkeyPatch):
    monkeypatch.setattr(
        "app.services.linkedin_publish.ensure_fresh_access_token",
        lambda: "test-access-token",
    )
    monkeypatch.setattr(
        "app.services.linkedin_publish.require_member_urn",
        lambda: "urn:li:person:abc123",
    )


def test_publish_text_share_ugc_payload(fake_limiter, fake_token_and_urn):
    captured = {}

    def fake_urlopen(req, timeout=None):
        captured["url"] = req.full_url
        captured["method"] = req.method
        captured["body"] = req.data
        resp = MagicMock()
        resp.read.return_value = b'{"id":"urn:li:ugcPost:1"}'
        resp.__enter__ = MagicMock(return_value=resp)
        resp.__exit__ = MagicMock(return_value=False)
        return resp

    with patch("urllib.request.urlopen", side_effect=fake_urlopen):
        out = publish_text_share("Hello world\n\n#one #two #three")

    assert out.get("id") == "urn:li:ugcPost:1"
    assert captured["url"] == "https://api.linkedin.com/v2/ugcPosts"
    assert b"urn:li:person:abc123" in captured["body"]
    assert b"Hello world" in captured["body"]


def test_publish_generated_variant(fake_limiter, fake_token_and_urn):
    lead_body = "x" * (MIN_POST_BODY_CHARS - 19) + "Body txt milestone."
    assert len(lead_body) == MIN_POST_BODY_CHARS

    def v():
        return LinkedInPostVariant(body=lead_body, hashtags=["a", "b", "c"])

    bundle = GeneratedPostsBundle(
        thought_leadership=v(),
        question_hook=v(),
        data_insight=v(),
    )

    with patch("urllib.request.urlopen") as m:
        resp = MagicMock()
        resp.read.return_value = b'{"id":"x"}'
        resp.__enter__.return_value = resp
        resp.__exit__.return_value = False
        m.return_value = resp
        publish_generated_variant(bundle, "thought_leadership")

    call = m.call_args[0][0]
    assert b"Body txt milestone" in call.data
