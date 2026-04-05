import importlib
import json
from pathlib import Path

import pytest

from api.main import app


def _reload_oauth(monkeypatch, tmp_path: Path):
    # The OAuth service imports credential constants from `app.config.settings` at module import time.
    # So we must reload settings BEFORE reloading linkedin_oauth.
    monkeypatch.setenv("LINKEDIN_CLIENT_ID", "test-client-id")
    monkeypatch.setenv("LINKEDIN_CLIENT_SECRET", "test-client-secret")

    import app.config.settings as settings_mod

    importlib.reload(settings_mod)

    import app.services.linkedin_oauth as linkedin_oauth

    importlib.reload(linkedin_oauth)

    tokens_path = tmp_path / "data" / "linkedin_tokens.json"

    def _tokens_path_override():
        return tokens_path

    monkeypatch.setattr(linkedin_oauth, "_tokens_path", _tokens_path_override)
    return linkedin_oauth


def test_routes_wired_in_fastapi():
    paths = {(r.path, tuple(sorted(getattr(r, "methods", []) or []))) for r in app.routes}
    # We just verify the router wiring exists.
    assert any(r.path == "/auth/linkedin" for r in app.routes)
    assert any(r.path == "/callback" for r in app.routes)
    assert len(paths) > 0


def test_auth_url_contains_scope_and_redirect(monkeypatch, tmp_path):
    linkedin_oauth = _reload_oauth(monkeypatch, tmp_path)

    url = linkedin_oauth.build_linkedin_authorization_url("state123")
    assert "https://www.linkedin.com/oauth/v2/authorization" in url
    assert "redirect_uri=http%3A%2F%2Flocalhost%3A8000%2Fcallback" in url
    assert "scope=" in url
    assert "w_member_social" in url
    assert "state=state123" in url


def test_token_storage_roundtrip(monkeypatch, tmp_path):
    linkedin_oauth = _reload_oauth(monkeypatch, tmp_path)

    tokens = {"access_token": "access-token", "refresh_token": "refresh-token", "expires_in": 3600}
    linkedin_oauth.save_tokens(tokens)

    loaded = linkedin_oauth.load_tokens()
    assert loaded is not None
    assert loaded["access_token"] == "access-token"
    assert loaded["refresh_token"] == "refresh-token"


def test_ensure_fresh_access_token_refreshes_when_expired(monkeypatch, tmp_path):
    linkedin_oauth = _reload_oauth(monkeypatch, tmp_path)

    expired_tokens = {
        "access_token": "old-access",
        "refresh_token": "refresh-token",
        "expires_in": 1,
        "obtained_at": 0.0,
    }
    monkeypatch.setattr(linkedin_oauth, "load_tokens", lambda: dict(expired_tokens))

    refreshed_tokens = {
        "access_token": "new-access",
        "refresh_token": "refresh-token",
        "expires_in": 3600,
        "obtained_at": 9999999999.0,
    }

    refreshed_called = {"called": False}

    def fake_refresh_access_token():
        refreshed_called["called"] = True
        return dict(refreshed_tokens)

    # Force refresh path.
    monkeypatch.setattr(linkedin_oauth, "token_is_expired_or_soon", lambda tokens, buffer_seconds=60: True)
    monkeypatch.setattr(linkedin_oauth, "refresh_access_token", fake_refresh_access_token)
    monkeypatch.setattr(linkedin_oauth, "save_tokens", lambda _tokens: None)

    # ensure_fresh_access_token reloads tokens after refresh; mock to return refreshed token dict.
    monkeypatch.setattr(linkedin_oauth, "load_tokens", lambda: dict(refreshed_tokens))

    access = linkedin_oauth.ensure_fresh_access_token()
    assert access == "new-access"
    assert refreshed_called["called"] is True


