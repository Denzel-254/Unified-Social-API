"""Post model for tracking published content."""

from datetime import datetime
from sqlalchemy import String, DateTime, ForeignKey, Text, JSON
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.core.database import Base


class Post(Base):
    """Tracks content published to social platforms."""
    
    __tablename__ = "posts"
    
    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False)
    content_text: Mapped[str] = mapped_column(Text, nullable=False)
    content_media_url: Mapped[str] = mapped_column(String(500), nullable=True)
    media_type: Mapped[str] = mapped_column(String(50), nullable=True)  # image, video, none
    platforms: Mapped[dict] = mapped_column(JSON, nullable=False)  # List of platforms published to
    status: Mapped[str] = mapped_column(String(50), default="pending")  # pending, processing, completed, failed
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    published_at: Mapped[datetime] = mapped_column(DateTime, nullable=True)
    
    # Relationships
    user = relationship("User", back_populates="posts")
    analytics = relationship("AnalyticsRecord", back_populates="post", cascade="all, delete-orphan")
    