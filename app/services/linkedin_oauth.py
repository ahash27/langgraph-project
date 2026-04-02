"""LinkedIn OAuth2 (Authorization Code grant) with lightweight token storage."""

from __future__ import annotations

import json
import os
import time
import uuid
import urllib.parse
import urllib.request
from pathlib import Path
from typing import Any, Dict, Optional

from dotenv import load_dotenv

AUTHORIZATION_ENDPOINT = "https://www.linkedin.com/oauth/v2/authorization"
TOKEN_ENDPOINT = "https://www.linkedin.com/oauth/v2/accessToken"

# Per your setup: must match the LinkedIn Developer Portal redirect URL exactly.
REDIRECT_URI = "http://localhost:8000/callback"

# MVP: personal member posting only. Org scopes come later.
# Override via LINKEDIN_SCOPES in .env when needed.
SCOPES_DEFAULT = "w_member_social"


def _get_scopes() -> str:
    _load_env_file()
    return os.getenv("LINKEDIN_SCOPES", SCOPES_DEFAULT)

# If token expires within this window, refresh before use.
REFRESH_BUFFER_SECONDS = 60

# In-memory CSRF-ish state store for the current process (dev-friendly).
_OAUTH_STATES: Dict[str, float] = {}


def _load_env_file() -> None:
    # Make dotenv loading independent of the server's current working directory.
    repo_root = Path(__file__).resolve().parents[2]
    load_dotenv(dotenv_path=repo_root / ".env")


def _require_linkedin_credentials() -> None:
    # Load from `.env` (absolute path). This makes the endpoint robust even if
    # the server started before the `.env` file was created.
    _load_env_file()

    client_id = os.getenv("LINKEDIN_CLIENT_ID")
    client_secret = os.getenv("LINKEDIN_CLIENT_SECRET")

    if not client_id or not client_secret:
        raise RuntimeError(
            "LinkedIn credentials missing. Set LINKEDIN_CLIENT_ID and LINKEDIN_CLIENT_SECRET in .env."
        )


def _get_linkedin_credentials() -> tuple[str, str]:
    _load_env_file()
    client_id = os.getenv("LINKEDIN_CLIENT_ID")
    client_secret = os.getenv("LINKEDIN_CLIENT_SECRET")
    if not client_id or not client_secret:
        raise RuntimeError(
            "LinkedIn credentials missing. Set LINKEDIN_CLIENT_ID and LINKEDIN_CLIENT_SECRET in .env."
        )
    return client_id, client_secret


def _tokens_path() -> Path:
    # Keep tokens outside .env; create folder at runtime.
    data_dir = Path("data")
    return data_dir / "linkedin_tokens.json"


def load_tokens() -> Optional[Dict[str, Any]]:
    path = _tokens_path()
    if not path.exists():
        return None
    return json.loads(path.read_text(encoding="utf-8"))


def save_tokens(tokens: Dict[str, Any]) -> None:
    path = _tokens_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(tokens, indent=2), encoding="utf-8")


def _compute_expiry(tokens: Dict[str, Any]) -> float:
    # LinkedIn returns `expires_in` (seconds) on initial token exchange/refresh.
    # We store `obtained_at` to compute a deterministic expires_at.
    expires_in = tokens.get("expires_in")
    obtained_at = tokens.get("obtained_at")
    if expires_in is None or obtained_at is None:
        return 0.0
    return float(obtained_at) + float(expires_in)


def token_is_expired_or_soon(tokens: Dict[str, Any], buffer_seconds: int = REFRESH_BUFFER_SECONDS) -> bool:
    expires_at = _compute_expiry(tokens)
    if expires_at == 0.0:
        return True
    return time.time() >= (expires_at - buffer_seconds)


def create_oauth_state(ttl_seconds: int = 600) -> str:
    state = uuid.uuid4().hex
    _OAUTH_STATES[state] = time.time() + ttl_seconds
    return state


def validate_oauth_state(state: str) -> bool:
    exp = _OAUTH_STATES.get(state)
    if not exp:
        return False
    if time.time() > exp:
        _OAUTH_STATES.pop(state, None)
        return False
    # One-time use.
    _OAUTH_STATES.pop(state, None)
    return True


def build_linkedin_authorization_url(state: str) -> str:
    _require_linkedin_credentials()
    client_id, _ = _get_linkedin_credentials()
    params = {
        "response_type": "code",
        "client_id": client_id,
        "redirect_uri": REDIRECT_URI,
        "scope": _get_scopes(),
        "state": state,
    }
    return f"{AUTHORIZATION_ENDPOINT}?{urllib.parse.urlencode(params)}"


def _post_form(url: str, form: Dict[str, str]) -> Dict[str, Any]:
    body = urllib.parse.urlencode(form).encode("utf-8")
    req = urllib.request.Request(
        url,
        data=body,
        headers={"Content-Type": "application/x-www-form-urlencoded"},
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            raw = resp.read().decode("utf-8")
            return json.loads(raw) if raw else {}
    except urllib.error.HTTPError as e:
        raw = e.read().decode("utf-8") if e.fp else ""
        raise RuntimeError(f"LinkedIn OAuth token exchange failed: {e.code} {raw}") from e


def exchange_code_for_tokens(code: str) -> Dict[str, Any]:
    _require_linkedin_credentials()
    client_id, client_secret = _get_linkedin_credentials()
    form = {
        "grant_type": "authorization_code",
        "code": code,
        "redirect_uri": REDIRECT_URI,
        "client_id": client_id,
        "client_secret": client_secret,
    }
    tokens = _post_form(TOKEN_ENDPOINT, form)

    # Normalize expiration + timekeeping so refresh checks work reliably.
    obtained_at = time.time()
    tokens["obtained_at"] = obtained_at
    if "expires_in" not in tokens:
        # LinkedIn should include it, but keep a safe default.
        tokens["expires_in"] = 0
    return tokens


def refresh_access_token() -> Dict[str, Any]:
    _require_linkedin_credentials()
    client_id, client_secret = _get_linkedin_credentials()

    tokens = load_tokens()
    if not tokens:
        raise RuntimeError("No stored LinkedIn tokens found. Run /auth/linkedin first.")

    refresh_token = tokens.get("refresh_token")
    if not refresh_token:
        raise RuntimeError("Stored LinkedIn tokens are missing `refresh_token`.")

    form = {
        "grant_type": "refresh_token",
        "refresh_token": str(refresh_token),
        "client_id": client_id,
        "client_secret": client_secret,
    }
    new_tokens = _post_form(TOKEN_ENDPOINT, form)
    # Preserve old refresh_token if LinkedIn doesn't return it every time.
    if "refresh_token" not in new_tokens:
        new_tokens["refresh_token"] = refresh_token

    new_tokens["obtained_at"] = time.time()
    if "expires_in" not in new_tokens:
        new_tokens["expires_in"] = tokens.get("expires_in", 0)
    save_tokens(new_tokens)
    return new_tokens


def ensure_fresh_access_token() -> str:
    tokens = load_tokens()
    if not tokens:
        raise RuntimeError("No stored LinkedIn tokens found. Run /auth/linkedin first.")

    if token_is_expired_or_soon(tokens):
        refresh_access_token()
        tokens = load_tokens() or {}

    access_token = tokens.get("access_token")
    if not access_token:
        raise RuntimeError("Stored LinkedIn tokens are missing `access_token`.")
    return str(access_token)

