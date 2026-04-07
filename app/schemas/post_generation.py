"""Pydantic models for LinkedIn post variants (SP-01) and prompt config loader."""

from __future__ import annotations

import json
import re
from pathlib import Path
from string import Template
from typing import Any, List

from pydantic import BaseModel, ConfigDict, Field, field_validator

MAX_POST_BODY_CHARS = 3000
MIN_HASHTAGS = 3
MAX_HASHTAGS = 5
_HASHTAG_TOKEN = re.compile(r"^[a-zA-Z0-9_]+$")


class LinkedInPostVariant(BaseModel):
    """One LinkedIn post draft: body + 3–5 hashtags (stored without # prefix)."""

    model_config = ConfigDict(str_strip_whitespace=True)

    body: str = Field(..., description="Post text only; hashtags listed separately.")
    hashtags: List[str] = Field(
        ...,
        description="3–5 topic hashtags, stored without leading #.",
    )

    @field_validator("body")
    @classmethod
    def body_within_limit(cls, v: str) -> str:
        if len(v) > MAX_POST_BODY_CHARS:
            raise ValueError(
                f"Post body must be at most {MAX_POST_BODY_CHARS} characters; got {len(v)}."
            )
        return v

    @field_validator("hashtags")
    @classmethod
    def normalize_and_count_hashtags(cls, v: List[str]) -> List[str]:
        cleaned: List[str] = []
        for raw in v:
            t = raw.strip()
            if t.startswith("#"):
                t = t[1:].strip()
            if not t:
                continue
            if not _HASHTAG_TOKEN.fullmatch(t):
                raise ValueError(
                    f"Invalid hashtag {raw!r}: use letters, digits, underscores only; one token each."
                )
            cleaned.append(t)

        seen: set[str] = set()
        unique: List[str] = []
        for t in cleaned:
            low = t.lower()
            if low not in seen:
                seen.add(low)
                unique.append(t)

        n = len(unique)
        if n < MIN_HASHTAGS or n > MAX_HASHTAGS:
            raise ValueError(
                f"Must have between {MIN_HASHTAGS} and {MAX_HASHTAGS} unique hashtags; got {n}."
            )
        return unique


class GeneratedPostsBundle(BaseModel):
    """Exactly three variants per trend (SP-01)."""

    thought_leadership: LinkedInPostVariant
    question_hook: LinkedInPostVariant
    data_insight: LinkedInPostVariant


class PostGenerationPromptConfig(BaseModel):
    """Prompt templates loaded from config file (not hardcoded in nodes)."""

    model_config = ConfigDict(str_strip_whitespace=True)

    brand_voice_system: str = Field(
        ...,
        description="System message: brand voice and global rules for the generator.",
    )
    user_prompt_template: str = Field(
        ...,
        description="User message template. Placeholders: $topic, $description, $related_queries.",
    )

    def render_user_prompt(
        self,
        *,
        topic: str,
        description: str = "",
        related_queries: str = "",
    ) -> str:
        """Fill the user template (safe: only $placeholders, no brace formatting)."""
        return Template(self.user_prompt_template).substitute(
            topic=topic or "",
            description=description or "",
            related_queries=related_queries or "",
        )


def _default_config_path() -> Path:
    return Path(__file__).resolve().parent.parent / "config" / "post_generation.json"


def load_post_generation_prompt_config(path: Path | None = None) -> PostGenerationPromptConfig:
    """Load prompt config from JSON next to other app config."""
    p = path or _default_config_path()
    raw: Any = json.loads(p.read_text(encoding="utf-8"))
    return PostGenerationPromptConfig.model_validate(raw)
