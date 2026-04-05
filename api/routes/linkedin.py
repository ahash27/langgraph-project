"""LinkedIn member posting (UGC) after OAuth."""

from typing import Any, Literal

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from app.services.linkedin_oauth import refresh_stored_member_urn
from app.services.linkedin_publish import publish_generated_variant, publish_text_share

router = APIRouter(prefix="/linkedin", tags=["linkedin"])


class PublishVariantRequest(BaseModel):
    """Client passes the `generated_posts` object from graph state + which variant to post."""

    variant: Literal["thought_leadership", "question_hook", "data_insight"]
    generated_posts: dict[str, Any] = Field(
        ...,
        description="Same shape as state['generated_posts'] / GeneratedPostsBundle.model_dump()",
    )


class PublishTextRequest(BaseModel):
    text: str = Field(..., min_length=1, max_length=3500)


@router.post("/publish-variant")
async def publish_variant(body: PublishVariantRequest):
    try:
        result = publish_generated_variant(body.generated_posts, body.variant)
        return {"ok": True, "linkedin": result}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e)) from e


@router.post("/publish-text")
async def publish_text(body: PublishTextRequest):
    try:
        result = publish_text_share(body.text)
        return {"ok": True, "linkedin": result}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e)) from e


@router.post("/refresh-member-urn")
async def refresh_member_urn():
    """Re-resolve urn:li:person:... (e.g. after adding openid/profile scopes)."""
    try:
        urn = refresh_stored_member_urn()
        return {"ok": True, "member_urn": urn}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e)) from e
