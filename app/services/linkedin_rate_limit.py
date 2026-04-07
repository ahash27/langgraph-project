"""
LinkedIn write-side throttling (Phase 4 / SP-01).

Official quotas depend on product and contract; defaults here are conservative.
Tune with LINKEDIN_MIN_POST_INTERVAL_SECONDS and LINKEDIN_MAX_POSTS_PER_DAY.

Use only around real publish calls (UGC Posts API, etc.), not around draft generation.
Wrap the HTTP call: ``limiter.run_throttled(lambda: post_to_linkedin(...))``.
"""

from __future__ import annotations

import json
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Callable, TypeVar

from app.config import settings

T = TypeVar("T")


def _utc_today() -> str:
    return datetime.now(timezone.utc).date().isoformat()


class LinkedInWriteRateLimiter:
    """Minimum spacing between successful writes + rolling daily cap (UTC day)."""

    def __init__(
        self,
        state_path: Path | None = None,
        *,
        min_interval_seconds: int | None = None,
        max_posts_per_day: int | None = None,
        clock: Callable[[], float] | None = None,
        sleeper: Callable[[float], None] | None = None,
    ) -> None:
        self.min_interval_seconds = (
            min_interval_seconds
            if min_interval_seconds is not None
            else settings.LINKEDIN_MIN_POST_INTERVAL_SECONDS
        )
        self.max_posts_per_day = (
            max_posts_per_day
            if max_posts_per_day is not None
            else settings.LINKEDIN_MAX_POSTS_PER_DAY
        )
        self._path = state_path or Path("data") / "linkedin_rate_limit_state.json"
        self._time = clock or time.time
        self._sleep = sleeper or time.sleep

    def _load(self) -> dict:
        if not self._path.exists():
            return {"day": None, "count": 0, "last_ts": 0.0}
        try:
            raw = json.loads(self._path.read_text(encoding="utf-8"))
            return {
                "day": raw.get("day"),
                "count": int(raw.get("count", 0)),
                "last_ts": float(raw.get("last_ts", 0.0)),
            }
        except (json.JSONDecodeError, OSError, TypeError, ValueError):
            return {"day": None, "count": 0, "last_ts": 0.0}

    def _save(self, state: dict) -> None:
        self._path.parent.mkdir(parents=True, exist_ok=True)
        self._path.write_text(
            json.dumps(
                {"day": state["day"], "count": state["count"], "last_ts": state["last_ts"]},
                indent=2,
            ),
            encoding="utf-8",
        )

    def _rollover(self, state: dict) -> None:
        today = _utc_today()
        if state.get("day") != today:
            state["day"] = today
            state["count"] = 0

    def run_throttled(self, fn: Callable[[], T]) -> T:
        """Sleep if needed, enforce daily cap, run ``fn``, then record only on success."""
        state = self._load()
        self._rollover(state)

        if state["count"] >= self.max_posts_per_day:
            raise RuntimeError(
                f"LinkedIn daily post cap reached ({self.max_posts_per_day} per UTC day). "
                "Raise LINKEDIN_MAX_POSTS_PER_DAY if your contract allows more."
            )

        now = self._time()
        last_ts = float(state.get("last_ts") or 0.0)
        if last_ts > 0:
            elapsed = now - last_ts
            need = self.min_interval_seconds - elapsed
            if need > 0:
                self._sleep(need)

        result = fn()

        state["count"] = int(state["count"]) + 1
        state["last_ts"] = self._time()
        self._save(state)
        return result


_limiter: LinkedInWriteRateLimiter | None = None


def get_linkedin_write_rate_limiter() -> LinkedInWriteRateLimiter:
    """Process-wide limiter (same state file)."""
    global _limiter
    if _limiter is None:
        _limiter = LinkedInWriteRateLimiter()
    return _limiter
