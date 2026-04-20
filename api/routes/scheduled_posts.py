"""API routes for scheduled posts."""

import json
from datetime import datetime, timezone
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.database.models import ScheduledPost, get_db
from app.services.scheduler import (
    cancel_scheduled_post,
    get_next_optimal_slot,
    schedule_post,
)

router = APIRouter(prefix="/scheduled-posts", tags=["scheduled-posts"])


class SchedulePostRequest(BaseModel):
    """Request to schedule a post."""

    variant: str = Field(..., pattern="^(thought_leadership|question_hook|data_insight)$")
    content: str = Field(..., min_length=1, max_length=3000)
    hashtags: List[str] = Field(default_factory=list)
    scheduled_time: Optional[str] = None  # ISO 8601 datetime string, if None uses next optimal slot


class SchedulePostResponse(BaseModel):
    """Response after scheduling a post."""

    id: int
    scheduled_time: str
    status: str
    message: str


class ScheduledPostInfo(BaseModel):
    """Information about a scheduled post."""

    id: int
    variant: str
    content: str
    hashtags: List[str]
    scheduled_time: str
    status: str
    created_at: str
    published_at: Optional[str] = None
    error_message: Optional[str] = None
    linkedin_post_urn: Optional[str] = None


@router.get("/next-optimal-slot", response_model=dict)
async def get_next_optimal_slot_endpoint():
    """Get the next optimal posting time (weekday 9-11am)."""
    next_slot = get_next_optimal_slot()
    return {
        "scheduled_time": next_slot.isoformat(),
        "timezone": "UTC",
        "message": "Next optimal posting slot (weekday 9am UTC)",
    }


@router.post("", response_model=SchedulePostResponse)
async def create_scheduled_post(
    request: SchedulePostRequest,
    db: Session = Depends(get_db),
):
    """
    Schedule a post for future publishing.
    If no scheduled_time provided, uses next optimal slot (weekday 9-11am).
    """
    try:
        # Parse or generate scheduled time
        if request.scheduled_time:
            try:
                scheduled_dt = datetime.fromisoformat(request.scheduled_time.replace("Z", "+00:00"))
                # Ensure it's in UTC
                if scheduled_dt.tzinfo is None:
                    scheduled_dt = scheduled_dt.replace(tzinfo=timezone.utc)
                else:
                    scheduled_dt = scheduled_dt.astimezone(timezone.utc)
            except ValueError as e:
                raise HTTPException(
                    status_code=400,
                    detail=f"Invalid datetime format. Use ISO 8601 format: {e}",
                )
            
            # Validate it's in the future
            if scheduled_dt <= datetime.now(timezone.utc):
                raise HTTPException(
                    status_code=400,
                    detail="Scheduled time must be in the future",
                )
        else:
            scheduled_dt = get_next_optimal_slot()

        # Create database record
        post = ScheduledPost(
            variant=request.variant,
            content=request.content,
            hashtags=json.dumps(request.hashtags),
            scheduled_time=scheduled_dt,
            status="pending",
        )
        db.add(post)
        db.commit()
        db.refresh(post)

        # Schedule with APScheduler
        job_id = schedule_post(post.id, scheduled_dt)

        return SchedulePostResponse(
            id=post.id,
            scheduled_time=scheduled_dt.isoformat(),
            status="pending",
            message=f"Post scheduled successfully (job: {job_id})",
        )

    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Failed to schedule post: {e}")


@router.get("", response_model=List[ScheduledPostInfo])
async def list_scheduled_posts(
    status: Optional[str] = None,
    db: Session = Depends(get_db),
):
    """
    List all scheduled posts, optionally filtered by status.
    Status can be: pending, published, cancelled, failed
    """
    query = db.query(ScheduledPost)
    
    if status:
        query = query.filter(ScheduledPost.status == status)
    
    posts = query.order_by(ScheduledPost.scheduled_time.desc()).all()
    
    return [
        ScheduledPostInfo(
            id=post.id,
            variant=post.variant,
            content=post.content,
            hashtags=json.loads(post.hashtags) if post.hashtags else [],
            scheduled_time=post.scheduled_time.isoformat(),
            status=post.status,
            created_at=post.created_at.isoformat(),
            published_at=post.published_at.isoformat() if post.published_at else None,
            error_message=post.error_message,
            linkedin_post_urn=post.linkedin_post_urn,
        )
        for post in posts
    ]


@router.get("/{post_id}", response_model=ScheduledPostInfo)
async def get_scheduled_post(
    post_id: int,
    db: Session = Depends(get_db),
):
    """Get details of a specific scheduled post."""
    post = db.query(ScheduledPost).filter(ScheduledPost.id == post_id).first()
    
    if not post:
        raise HTTPException(status_code=404, detail="Scheduled post not found")
    
    return ScheduledPostInfo(
        id=post.id,
        variant=post.variant,
        content=post.content,
        hashtags=json.loads(post.hashtags) if post.hashtags else [],
        scheduled_time=post.scheduled_time.isoformat(),
        status=post.status,
        created_at=post.created_at.isoformat(),
        published_at=post.published_at.isoformat() if post.published_at else None,
        error_message=post.error_message,
        linkedin_post_urn=post.linkedin_post_urn,
    )


@router.delete("/{post_id}")
async def cancel_scheduled_post_endpoint(
    post_id: int,
    db: Session = Depends(get_db),
):
    """Cancel a scheduled post (only if status is pending)."""
    post = db.query(ScheduledPost).filter(ScheduledPost.id == post_id).first()
    
    if not post:
        raise HTTPException(status_code=404, detail="Scheduled post not found")
    
    if post.status != "pending":
        raise HTTPException(
            status_code=400,
            detail=f"Cannot cancel post with status '{post.status}'. Only pending posts can be cancelled.",
        )
    
    # Cancel the scheduled job
    cancelled = cancel_scheduled_post(post_id)
    
    if cancelled:
        post.status = "cancelled"
        db.commit()
        return {"ok": True, "message": f"Scheduled post {post_id} cancelled successfully"}
    else:
        raise HTTPException(status_code=500, detail="Failed to cancel scheduled job")
