import json
from pathlib import Path
from unittest.mock import MagicMock

import pytest

from app.services.linkedin_rate_limit import LinkedInWriteRateLimiter, _utc_today


def test_run_throttled_records_success(tmp_path: Path):
    p = tmp_path / "state.json"
    lim = LinkedInWriteRateLimiter(
        state_path=p,
        min_interval_seconds=0,
        max_posts_per_day=10,
        clock=lambda: 1000.0,
        sleeper=lambda _: None,
    )
    assert lim.run_throttled(lambda: "ok") == "ok"
    data = json.loads(p.read_text(encoding="utf-8"))
    assert data["count"] == 1
    assert data["last_ts"] == 1000.0
    assert data["day"] == _utc_today()


def test_run_throttled_sleeps_for_interval(tmp_path: Path):
    p = tmp_path / "state.json"
    p.write_text(
        json.dumps({"day": _utc_today(), "count": 1, "last_ts": 1000.0}),
        encoding="utf-8",
    )
    sleeper = MagicMock()
    seq = iter([1500.0, 2000.0])

    def clock():
        return next(seq)

    lim = LinkedInWriteRateLimiter(
        state_path=p,
        min_interval_seconds=1000,
        max_posts_per_day=10,
        clock=clock,
        sleeper=sleeper,
    )
    lim.run_throttled(lambda: None)
    sleeper.assert_called_once()
    assert abs(sleeper.call_args[0][0] - 500.0) < 0.01


def test_daily_cap_raises(tmp_path: Path):
    p = tmp_path / "state.json"
    p.write_text(
        json.dumps({"day": _utc_today(), "count": 2, "last_ts": 1.0}),
        encoding="utf-8",
    )
    lim = LinkedInWriteRateLimiter(
        state_path=p,
        min_interval_seconds=0,
        max_posts_per_day=2,
        clock=lambda: 999.0,
        sleeper=lambda _: None,
    )
    with pytest.raises(RuntimeError, match="daily post cap"):
        lim.run_throttled(lambda: None)


def test_failed_callable_does_not_increment(tmp_path: Path):
    p = tmp_path / "state.json"
    lim = LinkedInWriteRateLimiter(
        state_path=p,
        min_interval_seconds=0,
        max_posts_per_day=10,
        clock=lambda: 1.0,
        sleeper=lambda _: None,
    )

    def boom():
        raise ValueError("boom")

    with pytest.raises(ValueError, match="boom"):
        lim.run_throttled(boom)

    assert not p.exists() or json.loads(p.read_text(encoding="utf-8")).get("count", 0) == 0
