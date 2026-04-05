import json
from pathlib import Path
from unittest.mock import MagicMock

import pytest
from langchain_core.messages import AIMessage

from app.services.generate_posts import generate_posts_bundle


def _valid_bundle_json() -> str:
    v = lambda: {"body": "Short post text here.", "hashtags": ["one", "two", "three"]}
    return json.dumps(
        {
            "thought_leadership": v(),
            "question_hook": {**v(), "hashtags": ["a", "b", "c", "d"]},
            "data_insight": {**v(), "hashtags": ["x", "y", "z", "w", "q"]},
        }
    )


def test_generate_posts_bundle_parses_fenced_json(tmp_path: Path):
    cfg = {
        "brand_voice_system": "You are a test assistant.",
        "user_prompt_template": "Topic: $topic",
    }
    p = tmp_path / "cfg.json"
    p.write_text(json.dumps(cfg), encoding="utf-8")

    raw = "```json\n" + _valid_bundle_json() + "\n```"
    mock_llm = MagicMock()
    mock_llm.invoke = MagicMock(return_value=AIMessage(content=raw))

    bundle = generate_posts_bundle(
        topic="AI trends",
        config_path=p,
        model=mock_llm,
        max_retries=0,
    )
    assert bundle.thought_leadership.body.startswith("Short post")
    mock_llm.invoke.assert_called_once()


def test_generate_posts_bundle_retries_then_succeeds(tmp_path: Path):
    cfg = {
        "brand_voice_system": "sys",
        "user_prompt_template": "T=$topic",
    }
    p = Path(tmp_path / "cfg.json")
    p.write_text(json.dumps(cfg), encoding="utf-8")

    bad = "not json"
    good = _valid_bundle_json()
    mock_llm = MagicMock()
    mock_llm.invoke = MagicMock(side_effect=[AIMessage(content=bad), AIMessage(content=good)])

    bundle = generate_posts_bundle(topic="x", config_path=p, model=mock_llm, max_retries=1)
    assert bundle.question_hook.hashtags == ["a", "b", "c", "d"]
    assert mock_llm.invoke.call_count == 2


def test_generate_posts_bundle_fails_after_retries(tmp_path: Path):
    cfg = {"brand_voice_system": "s", "user_prompt_template": "T=$topic"}
    p = Path(tmp_path / "cfg.json")
    p.write_text(json.dumps(cfg), encoding="utf-8")

    mock_llm = MagicMock()
    mock_llm.invoke = MagicMock(return_value=AIMessage(content="nope"))

    with pytest.raises(RuntimeError, match="Failed to generate valid posts"):
        generate_posts_bundle(topic="x", config_path=p, model=mock_llm, max_retries=1)
