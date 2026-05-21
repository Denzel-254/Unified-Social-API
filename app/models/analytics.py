"""Analytics data model."""

from datetime import datetime
from sqlalchemy import String, DateTime, ForeignKey, Integer
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.core.database import Base


class AnalyticsRecord(Base):
    """Stores analytics data from social platforms."""
    
    __tablename__ = "analytics_records"
    
    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    post_id: Mapped[int] = mapped_column(ForeignKey("posts.id"), nullable=False)
    platform: Mapped[str] = mapped_column(String(50), nullable=False)
    platform_post_id: Mapped[str] = mapped_column(String(255), nullable=True)
    
    # Metrics
    reach: Mapped[int] = mapped_column(Integer, default=0)
    impressions: Mapped[int] = mapped_column(Integer, default=0)
    likes: Mapped[int] = mapped_column(Integer, default=0)
    comments: Mapped[int] = mapped_column(Integer, default=0)
    shares: Mapped[int] = mapped_column(Integer, default=0)
    
    collected_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    
    # Relationships
    post = relationship("Post", back_populates="analytics")