"""APScheduler service for scheduled post publishing."""

import json
import logging
from datetime import datetime, timezone
from typing import Optional

from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.date import DateTrigger
from sqlalchemy.orm import Session

from app.database.models import ScheduledPost, SessionLocal
from app.nodes.publish_post_node import publish_post

logger = logging.getLogger(__name__)

# Global scheduler instance
_scheduler: Optional[BackgroundScheduler] = None


def get_scheduler() -> BackgroundScheduler:
    """Get or create the global scheduler instance."""
    global _scheduler
    if _scheduler is None:
        _scheduler = BackgroundScheduler(timezone="UTC")
        _scheduler.start()
        logger.info("APScheduler started")
    return _scheduler


def stop_scheduler():
    """Stop the scheduler gracefully."""
    global _scheduler
    if _scheduler is not None:
        _scheduler.shutdown()
        _scheduler = None
        logger.info("APScheduler stopped")


def publish_scheduled_post(post_id: int):
    """
    Job function to publish a scheduled post.
    Called by APScheduler at the scheduled time.
    """
    db: Session = SessionLocal()
    try:
        post = db.query(ScheduledPost).filter(ScheduledPost.id == post_id).first()
        if not post:
            logger.error(f"Scheduled post {post_id} not found")
            return

        if post.status != "pending":
            logger.warning(f"Post {post_id} status is {post.status}, skipping")
            return

        # Prepare state for publish_post node
        hashtags = json.loads(post.hashtags) if post.hashtags else []
        tags_str = " ".join(f"#{h}" for h in hashtags)
        content = f"{post.content}\n\n{tags_str}".strip()

        state = {
            "approved_for_publish": True,
            "approved_content": content,
            "publish_draft_text": content,
            "selected_variant": post.variant,
            "execution_history": [],
        }

        # Publish the post
        result_state = publish_post(state)

        if result_state.get("publish_post_status") == "completed":
            post.status = "published"
            post.published_at = datetime.utcnow()
            post.linkedin_post_urn = result_state.get("linkedin_post_urn")
            logger.info(f"Successfully published scheduled post {post_id}")
        else:
            post.status = "failed"
            post.error_message = result_state.get("publish_post_error", "Unknown error")
            logger.error(f"Failed to publish post {post_id}: {post.error_message}")

        db.commit()

    except Exception as e:
        logger.exception(f"Error publishing scheduled post {post_id}")
        post.status = "failed"
        post.error_message = str(e)
        db.commit()
    finally:
        db.close()


def schedule_post(
    post_id: int,
    scheduled_time: datetime,
) -> str:
    """
    Schedule a post for publishing at a specific time.
    
    Args:
        post_id: Database ID of the scheduled post
        scheduled_time: UTC datetime when to publish
        
    Returns:
        Job ID from APScheduler
    """
    scheduler = get_scheduler()
    
    # Create a unique job ID
    job_id = f"post_{post_id}"
    
    # Remove existing job if any
    if scheduler.get_job(job_id):
        scheduler.remove_job(job_id)
    
    # Schedule the job
    job = scheduler.add_job(
        publish_scheduled_post,
        trigger=DateTrigger(run_date=scheduled_time),
        args=[post_id],
        id=job_id,
        name=f"Publish post {post_id}",
        replace_existing=True,
    )
    
    logger.info(f"Scheduled post {post_id} for {scheduled_time} UTC (job: {job_id})")
    return job_id


def cancel_scheduled_post(post_id: int) -> bool:
    """
    Cancel a scheduled post.
    
    Args:
        post_id: Database ID of the scheduled post
        
    Returns:
        True if cancelled successfully, False otherwise
    """
    scheduler = get_scheduler()
    job_id = f"post_{post_id}"
    
    try:
        if scheduler.get_job(job_id):
            scheduler.remove_job(job_id)
            logger.info(f"Cancelled scheduled post {post_id}")
            return True
        else:
            logger.warning(f"No scheduled job found for post {post_id}")
            return False
    except Exception as e:
        logger.exception(f"Error cancelling scheduled post {post_id}")
        return False


def get_next_optimal_slot() -> datetime:
    """
    Get the next optimal posting time (weekday 9-11am local time).
    For simplicity, returns next weekday at 9am UTC.
    In production, this should consider user's timezone.
    """
    now = datetime.now(timezone.utc)
    next_slot = now.replace(hour=9, minute=0, second=0, microsecond=0)
    
    # If it's past 9am today, move to tomorrow
    if now.hour >= 9:
        from datetime import timedelta
        next_slot += timedelta(days=1)
    
    # Skip weekends
    while next_slot.weekday() >= 5:  # 5=Saturday, 6=Sunday
        from datetime import timedelta
        next_slot += timedelta(days=1)
    
    return next_slot
