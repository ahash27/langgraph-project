import json
from pathlib import Path

import pytest
from pydantic import ValidationError

from app.schemas.post_generation import (
    GeneratedPostsBundle,
    LinkedInPostVariant,
    MAX_POST_BODY_CHARS,
    PostGenerationPromptConfig,
    load_post_generation_prompt_config,
)


def _variant(body: str = "Hello.", tags: list[str] | None = None):
    tags = tags or ["one", "two", "three"]
    return {"body": body, "hashtags": tags}


def test_generated_posts_bundle_valid():
    data = {
        "thought_leadership": _variant(),
        "question_hook": _variant(tags=["a", "b", "c", "d"]),
        "data_insight": _variant(tags=["x", "y", "z", "w", "v"]),
    }
    bundle = GeneratedPostsBundle.model_validate(data)
    assert bundle.question_hook.hashtags == ["a", "b", "c", "d"]


def test_hashtag_normalization_strips_hash_and_dedupes():
    v = LinkedInPostVariant.model_validate(
        {"body": "x", "hashtags": ["#A", "a", "B", "c"]}
    )
    assert v.hashtags == ["A", "B", "c"]


def test_hashtag_count_too_few():
    with pytest.raises(ValueError, match="3 and 5"):
        LinkedInPostVariant.model_validate({"body": "x", "hashtags": ["a", "b"]})


def test_hashtag_count_too_many():
    with pytest.raises(ValueError, match="3 and 5"):
        LinkedInPostVariant.model_validate(
            {"body": "x", "hashtags": ["a", "b", "c", "d", "e", "f"]}
        )


def test_body_over_limit():
    with pytest.raises(ValueError, match="3000"):
        LinkedInPostVariant.model_validate(
            {"body": "x" * (MAX_POST_BODY_CHARS + 1), "hashtags": ["a", "b", "c"]}
        )


def test_invalid_hashtag_characters():
    with pytest.raises(ValueError, match="Invalid hashtag"):
        LinkedInPostVariant.model_validate(
            {"body": "ok", "hashtags": ["bad tag", "b", "c"]}
        )


def test_load_default_prompt_config():
    cfg = load_post_generation_prompt_config()
    assert "LinkedIn" in cfg.brand_voice_system
    assert "$topic" in cfg.user_prompt_template
    out = cfg.render_user_prompt(topic="AI", description="trending", related_queries="q1, q2")
    assert "AI" in out and "trending" in out and "q1" in out


def test_load_custom_config_path(tmp_path: Path):
    p = tmp_path / "cfg.json"
    p.write_text(
        json.dumps(
            {
                "brand_voice_system": "sys",
                "user_prompt_template": "T=$topic D=$description R=$related_queries",
            }
        ),
        encoding="utf-8",
    )
    cfg = load_post_generation_prompt_config(p)
    assert cfg.render_user_prompt(topic="1", description="2", related_queries="3") == "T=1 D=2 R=3"


def test_post_generation_prompt_config_validation():
    with pytest.raises(ValidationError):
        PostGenerationPromptConfig.model_validate({"brand_voice_system": "x"})
