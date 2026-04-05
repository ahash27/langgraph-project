"""Publish a member text share to LinkedIn (UGC Posts v2)."""

from __future__ import annotations

import json
import urllib.error
import urllib.request
from typing import Any, Dict, List, Literal

from app.schemas.post_generation import GeneratedPostsBundle, LinkedInPostVariant
from app.services.linkedin_oauth import ensure_fresh_access_token, require_member_urn
from app.services.linkedin_rate_limit import get_linkedin_write_rate_limiter

UGC_POSTS_URL = "https://api.linkedin.com/v2/ugcPosts"

VariantName = Literal["thought_leadership", "question_hook", "data_insight"]


def _share_text(body: str, hashtags: List[str]) -> str:
    tags = " ".join(f"#{h}" for h in hashtags)
    return f"{body.strip()}\n\n{tags}".strip()


def _ugc_payload(author_urn: str, share_text: str) -> Dict[str, Any]:
    return {
        "author": author_urn,
        "lifecycleState": "PUBLISHED",
        "specificContent": {
            "com.linkedin.ugc.ShareContent": {
                "shareCommentary": {"text": share_text},
                "shareMediaCategory": "NONE",
            }
        },
        "visibility": {"com.linkedin.ugc.MemberNetworkVisibility": "PUBLIC"},
    }


def _post_ugc(access_token: str, payload: Dict[str, Any]) -> Dict[str, Any]:
    data = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(
        UGC_POSTS_URL,
        data=data,
        headers={
            "Authorization": f"Bearer {access_token}",
            "Content-Type": "application/json",
            "X-Restli-Protocol-Version": "2.0.0",
        },
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=60) as resp:
            raw = resp.read().decode("utf-8")
            out: object = json.loads(raw) if raw else {}
            return out if isinstance(out, dict) else {"raw": raw}
    except urllib.error.HTTPError as e:
        err = e.read().decode("utf-8") if e.fp else ""
        raise RuntimeError(f"LinkedIn ugcPosts failed: {e.code} {err}") from e


def publish_text_share(text: str) -> Dict[str, Any]:
    """
    Post plain text (already includes hashtags if desired).
    Refreshes token, resolves author URN, applies write rate limit, then POSTs.
    """
    limiter = get_linkedin_write_rate_limiter()

    def _call() -> Dict[str, Any]:
        token = ensure_fresh_access_token()
        author = require_member_urn()
        payload = _ugc_payload(author, text)
        return _post_ugc(token, payload)

    return limiter.run_throttled(_call)


def publish_generated_variant(
    bundle: GeneratedPostsBundle | dict[str, Any],
    variant: VariantName,
) -> Dict[str, Any]:
    """Pick one SP-01 variant and publish."""
    b = bundle if isinstance(bundle, GeneratedPostsBundle) else GeneratedPostsBundle.model_validate(bundle)
    v: LinkedInPostVariant = getattr(b, variant)
    text = _share_text(v.body, v.hashtags)
    return publish_text_share(text)
