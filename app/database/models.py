"""Database models for scheduled posts."""

from datetime import datetime
from typing import Optional

from sqlalchemy import Column, DateTime, Integer, String, Text, create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

Base = declarative_base()


class ScheduledPost(Base):
    """Model for scheduled LinkedIn posts."""

    __tablename__ = "scheduled_posts"

    id = Column(Integer, primary_key=True, index=True)
    variant = Column(String(50), nullable=False)  # thought_leadership, question_hook, data_insight
    content = Column(Text, nullable=False)
    hashtags = Column(Text, nullable=True)  # JSON string of hashtags
    scheduled_time = Column(DateTime, nullable=False)  # UTC timestamp
    status = Column(String(20), default="pending")  # pending, published, cancelled, failed
    created_at = Column(DateTime, default=datetime.utcnow)
    published_at = Column(DateTime, nullable=True)
    error_message = Column(Text, nullable=True)
    linkedin_post_urn = Column(String(255), nullable=True)


# Database setup
DATABASE_URL = "sqlite:///./data/langgraph.db"
engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def init_db():
    """Initialize database tables."""
    Base.metadata.create_all(bind=engine)


def get_db():
    """Get database session."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
