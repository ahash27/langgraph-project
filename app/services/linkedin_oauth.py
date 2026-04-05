"""LinkedIn OAuth2, token storage, member URN for UGC posts."""

from __future__ import annotations

import base64
import json
import os
import time
import uuid
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path
from typing import Any, Dict, Optional, TypedDict, cast

from dotenv import load_dotenv

AUTHORIZATION_ENDPOINT = "https://www.linkedin.com/oauth/v2/authorization"
TOKEN_ENDPOINT = "https://www.linkedin.com/oauth/v2/accessToken"
USERINFO_ENDPOINT = "https://api.linkedin.com/v2/userinfo"
ME_ENDPOINT = "https://api.linkedin.com/v2/me?projection=(id)"

REDIRECT_URI = "http://localhost:8000/callback"
# Posting + identity: openid/profile for userinfo; trim in .env if your app lacks OpenID product.
SCOPES_DEFAULT = "w_member_social openid profile"

REFRESH_BUFFER_SECONDS = 60
_OAUTH_STATES: Dict[str, float] = {}


class LinkedInTokenEndpointResponse(TypedDict, total=False):
    access_token: str
    expires_in: int
    refresh_token: str
    scope: str
    token_type: str
    id_token: str


class StoredLinkedInTokens(TypedDict, total=False):
    access_token: str
    expires_in: int
    obtained_at: float
    refresh_token: str
    scope: str
    token_type: str
    member_urn: str


def _get_scopes() -> str:
    _load_env_file()
    return os.getenv("LINKEDIN_SCOPES", SCOPES_DEFAULT)


def _load_env_file() -> None:
    repo_root = Path(__file__).resolve().parents[2]
    load_dotenv(dotenv_path=repo_root / ".env")


def _require_linkedin_credentials() -> None:
    _load_env_file()
    if not os.getenv("LINKEDIN_CLIENT_ID") or not os.getenv("LINKEDIN_CLIENT_SECRET"):
        raise RuntimeError(
            "Set LINKEDIN_CLIENT_ID and LINKEDIN_CLIENT_SECRET in .env."
        )


def _get_linkedin_credentials() -> tuple[str, str]:
    _load_env_file()
    cid = os.getenv("LINKEDIN_CLIENT_ID")
    sec = os.getenv("LINKEDIN_CLIENT_SECRET")
    if not cid or not sec:
        raise RuntimeError(
            "Set LINKEDIN_CLIENT_ID and LINKEDIN_CLIENT_SECRET in .env."
        )
    return cid, sec


def _tokens_path() -> Path:
    return Path("data") / "linkedin_tokens.json"


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
    ex = tokens.get("expires_in")
    ob = tokens.get("obtained_at")
    if ex is None or ob is None:
        return 0.0
    return float(ob) + float(ex)


def token_is_expired_or_soon(
    tokens: StoredLinkedInTokens, buffer_seconds: int = REFRESH_BUFFER_SECONDS
) -> bool:
    exp = _compute_expiry(tokens)
    if exp == 0.0:
        return True
    return time.time() >= (exp - buffer_seconds)


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
        err = e.read().decode("utf-8") if e.fp else ""
        raise RuntimeError(f"LinkedIn token exchange failed: {e.code} {err}") from e


def _linkedin_api_version() -> str:
    _load_env_file()
    v = (os.getenv("LINKEDIN_REST_VERSION") or "202504").strip()
    return v or "202504"


def _member_urn_from_id_token(id_token: str | None) -> Optional[str]:
    """OIDC id_token from token endpoint includes `sub` (member id); avoids /userinfo and /v2/me."""
    if not id_token or not str(id_token).strip():
        return None
    parts = str(id_token).split(".")
    if len(parts) != 3:
        return None
    payload_b64 = parts[1]
    pad = (4 - len(payload_b64) % 4) % 4
    payload_b64 += "=" * pad
    payload_b64 = payload_b64.replace("-", "+").replace("_", "/")
    try:
        raw = base64.b64decode(payload_b64)
        obj: object = json.loads(raw.decode("utf-8"))
        if not isinstance(obj, dict):
            return None
        sub = obj.get("sub")
        if not sub:
            return None
        s = str(sub)
        return s if s.startswith("urn:") else f"urn:li:person:{s}"
    except (json.JSONDecodeError, ValueError, UnicodeDecodeError):
        return None


def _http_get_json(url: str, headers: dict[str, str]) -> dict[str, Any]:
    req = urllib.request.Request(url, headers=headers, method="GET")
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            raw = resp.read().decode("utf-8")
            out: object = json.loads(raw) if raw else {}
            return out if isinstance(out, dict) else {}
    except urllib.error.HTTPError as e:
        err = e.read().decode("utf-8") if e.fp else ""
        raise RuntimeError(f"LinkedIn API GET failed: {e.code} {err}") from e


def fetch_member_urn(access_token: str) -> str:
    """
    Resolve urn:li:person:... for the authorized member.
    Tries OpenID userinfo first (Bearer only per LinkedIn docs), then v2/me.
    """
    userinfo_err: Optional[str] = None
    try:
        data = _http_get_json(
            USERINFO_ENDPOINT,
            {"Authorization": f"Bearer {access_token}"},
        )
        sub = data.get("sub")
        if sub:
            s = str(sub)
            return s if s.startswith("urn:") else f"urn:li:person:{s}"
    except RuntimeError as e:
        userinfo_err = str(e)

    try:
        data = _http_get_json(
            ME_ENDPOINT,
            {
                "Authorization": f"Bearer {access_token}",
                "X-Restli-Protocol-Version": "2.0.0",
                "LinkedIn-Version": _linkedin_api_version(),
            },
        )
    except RuntimeError as e:
        me_err = str(e)
        hint = (
            "Enable product 'Sign In with LinkedIn using OpenID Connect', request scopes "
            "openid+profile (+ w_member_social), then visit /auth/linkedin again. "
            "If it still fails, the token exchange should return id_token — re-auth after pulling latest app code."
        )
        parts = [me_err]
        if userinfo_err:
            parts.append(f"userinfo: {userinfo_err}")
        parts.append(hint)
        raise RuntimeError(" | ".join(parts)) from e

    pid = data.get("id")
    if not pid:
        raise RuntimeError(
            "LinkedIn /v2/me returned no id. Enable OpenID Connect product and openid+profile; re-authorize."
        )
    return f"urn:li:person:{pid}"


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
    urn = _member_urn_from_id_token(tokens.get("id_token"))
    if urn:
        stored["member_urn"] = urn
    else:
        try:
            stored["member_urn"] = fetch_member_urn(stored["access_token"])
        except Exception:
            pass
    return stored


def refresh_access_token() -> StoredLinkedInTokens:
    _require_linkedin_credentials()
    client_id, client_secret = _get_linkedin_credentials()
    tokens = load_tokens()
    if not tokens:
        raise RuntimeError("No stored LinkedIn tokens. Run /auth/linkedin first.")
    rt = tokens.get("refresh_token")
    if not rt:
        raise RuntimeError("Stored tokens missing refresh_token.")
    form = {
        "grant_type": "refresh_token",
        "refresh_token": str(rt),
        "client_id": client_id,
        "client_secret": client_secret,
    }
    new_api = _post_form(TOKEN_ENDPOINT, form)
    merged = _merge_stored_tokens(new_api, prior_refresh=str(rt))
    if not merged.get("access_token"):
        raise RuntimeError("LinkedIn refresh missing access_token.")
    urn_jwt = _member_urn_from_id_token(new_api.get("id_token"))
    if urn_jwt:
        merged["member_urn"] = urn_jwt
    elif tokens.get("member_urn"):
        merged["member_urn"] = tokens["member_urn"]
    save_tokens(merged)
    return merged


def ensure_fresh_access_token() -> str:
    tokens = load_tokens()
    if not tokens:
        raise RuntimeError("No stored LinkedIn tokens. Run /auth/linkedin first.")
    if token_is_expired_or_soon(tokens):
        refresh_access_token()
        tokens = load_tokens()
    if not tokens:
        raise RuntimeError("No tokens after refresh.")
    at = tokens.get("access_token")
    if not at:
        raise RuntimeError("Missing access_token.")
    return str(at)


def require_member_urn() -> str:
    """Return stored member URN or fetch with current access token and persist."""
    tokens = load_tokens()
    if not tokens:
        raise RuntimeError("No stored LinkedIn tokens. Run /auth/linkedin first.")
    urn = tokens.get("member_urn")
    if urn:
        return str(urn)
    token = ensure_fresh_access_token()
    urn = fetch_member_urn(token)
    tokens["member_urn"] = urn
    save_tokens(tokens)
    return urn


def refresh_stored_member_urn() -> str:
    """Re-fetch member URN (e.g. after adding openid scopes)."""
    token = ensure_fresh_access_token()
    urn = fetch_member_urn(token)
    tokens = load_tokens() or {}
    tokens["member_urn"] = urn
    save_tokens(tokens)
    return urn
