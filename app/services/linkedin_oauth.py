"""LinkedIn OAuth2 (Authorization Code grant) with lightweight token storage."""

from __future__ import annotations

import json
import os
import time
import uuid
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path
from typing import Dict, Optional, TypedDict, cast

from dotenv import load_dotenv

AUTHORIZATION_ENDPOINT = "https://www.linkedin.com/oauth/v2/authorization"
TOKEN_ENDPOINT = "https://www.linkedin.com/oauth/v2/accessToken"

# Per your setup: must match the LinkedIn Developer Portal redirect URL exactly.
REDIRECT_URI = "http://localhost:8000/callback"

# MVP: personal member posting only. Org scopes come later.
# Override via LINKEDIN_SCOPES in .env when needed.
SCOPES_DEFAULT = "w_member_social"

# If token expires within this window, refresh before use.
REFRESH_BUFFER_SECONDS = 60

# In-memory CSRF-ish state store for the current process (dev-friendly).
_OAUTH_STATES: Dict[str, float] = {}


class LinkedInTokenEndpointResponse(TypedDict, total=False):
    """JSON body from LinkedIn's accessToken endpoint."""

    access_token: str
    expires_in: int
    refresh_token: str
    scope: str
    token_type: str


class StoredLinkedInTokens(TypedDict, total=False):
    """Tokens we persist; includes LinkedIn fields plus obtained_at."""

    access_token: str
    expires_in: int
    obtained_at: float
    refresh_token: str
    scope: str
    token_type: str


def _get_scopes() -> str:
    _load_env_file()
    return os.getenv("LINKEDIN_SCOPES", SCOPES_DEFAULT)


def _load_env_file() -> None:
    # Make dotenv loading independent of the server's current working directory.
    repo_root = Path(__file__).resolve().parents[2]
    load_dotenv(dotenv_path=repo_root / ".env")


def _require_linkedin_credentials() -> None:
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


def load_tokens() -> Optional[StoredLinkedInTokens]:
    path = _tokens_path()
    if not path.exists():
        return None
    raw: object = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(raw, dict):
        return None
    return cast(StoredLinkedInTokens, raw)


def save_tokens(tokens: StoredLinkedInTokens) -> None:
    path = _tokens_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(tokens, indent=2), encoding="utf-8")


def _compute_expiry(tokens: StoredLinkedInTokens) -> float:
    expires_in = tokens.get("expires_in")
    obtained_at = tokens.get("obtained_at")
    if expires_in is None or obtained_at is None:
        return 0.0
    return float(obtained_at) + float(expires_in)


def token_is_expired_or_soon(
    tokens: StoredLinkedInTokens, buffer_seconds: int = REFRESH_BUFFER_SECONDS
) -> bool:
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


def _post_form(url: str, form: Dict[str, str]) -> LinkedInTokenEndpointResponse:
    body = urllib.parse.urlencode(form).encode("utf-8")
    req = urllib.request.Request(
        url,
        data=body,
        headers={"Content-Type": "application/x-www-form-urlencoded"},
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            raw_txt = resp.read().decode("utf-8")
            payload: object = json.loads(raw_txt) if raw_txt else {}
            if not isinstance(payload, dict):
                return {}
            return cast(LinkedInTokenEndpointResponse, payload)
    except urllib.error.HTTPError as e:
        raw_err = e.read().decode("utf-8") if e.fp else ""
        raise RuntimeError(f"LinkedIn OAuth token exchange failed: {e.code} {raw_err}") from e


def _merge_stored_tokens(
    api: LinkedInTokenEndpointResponse, prior_refresh: Optional[str] = None
) -> StoredLinkedInTokens:
    out: StoredLinkedInTokens = {}
    if "access_token" in api:
        out["access_token"] = api["access_token"]
    if "expires_in" in api:
        out["expires_in"] = int(api["expires_in"])
    if "refresh_token" in api:
        out["refresh_token"] = api["refresh_token"]
    elif prior_refresh is not None:
        out["refresh_token"] = prior_refresh
    if "scope" in api:
        out["scope"] = api["scope"]
    if "token_type" in api:
        out["token_type"] = api["token_type"]
    out["obtained_at"] = time.time()
    if "expires_in" not in out:
        out["expires_in"] = 0
    return out


def exchange_code_for_tokens(code: str) -> StoredLinkedInTokens:
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
    stored = _merge_stored_tokens(tokens)
    if not stored.get("access_token"):
        raise RuntimeError("LinkedIn token response missing access_token.")
    return stored


def refresh_access_token() -> StoredLinkedInTokens:
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
    new_api = _post_form(TOKEN_ENDPOINT, form)
    merged = _merge_stored_tokens(new_api, prior_refresh=str(refresh_token))
    if not merged.get("access_token"):
        raise RuntimeError("LinkedIn refresh response missing access_token.")
    save_tokens(merged)
    return merged


def ensure_fresh_access_token() -> str:
    tokens = load_tokens()
    if not tokens:
        raise RuntimeError("No stored LinkedIn tokens found. Run /auth/linkedin first.")

    if token_is_expired_or_soon(tokens):
        refresh_access_token()
        tokens = load_tokens()

    if not tokens:
        raise RuntimeError("No stored LinkedIn tokens found after refresh.")

    access_token = tokens.get("access_token")
    if not access_token:
        raise RuntimeError("Stored LinkedIn tokens are missing `access_token`.")
    return str(access_token)
