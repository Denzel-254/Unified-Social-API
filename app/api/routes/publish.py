"""Publishing endpoints - Day 3: Facebook & Instagram Integration."""

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from typing import List, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.database import get_db
from app.services.publish_service import PublishService

router = APIRouter(prefix="/publish", tags=["publishing"])

# Temporary user ID (will be replaced with real auth in later days)
CURRENT_USER_ID = 1


class PublishRequest(BaseModel):
    """Request model for publishing content to platforms."""
    platforms: List[str]
    content: str
    media_url: Optional[str] = None
    media_type: Optional[str] = None  # "image", "video", or None


class PublishResponse(BaseModel):
    """Response model for publishing results."""
    message: str
    results: dict
    total_platforms: int
    successful: int


@router.post("/", response_model=PublishResponse)
async def publish_content(
    request: PublishRequest,
    db: AsyncSession = Depends(get_db)
):
    """Publish content to selected platforms."""
    
    # Validate that platforms list is not empty
    if not request.platforms:
        raise HTTPException(
            status_code=400,
            detail="At least one platform must be specified."
        )
    
    # Validate content is not empty
    if not request.content or len(request.content.strip()) == 0:
        raise HTTPException(
            status_code=400,
            detail="Content cannot be empty."
        )
    
    # FIXED: Only validate media_type if media_url is provided
    if request.media_url:
        # If media_url is provided, media_type is required
        if not request.media_type:
            raise HTTPException(
                status_code=400,
                detail="media_type is required when media_url is provided."
            )
        
        # Validate media_type is valid (only when media_type has a value)
        if request.media_type not in ["image", "video"]:
            raise HTTPException(
                status_code=400,
                detail="media_type must be 'image' or 'video'."
            )
    # If no media_url, we ignore media_type (can be null or anything)
    
    # Validate platforms are supported (Day 3 supports Facebook & Instagram)
    supported_platforms = ["facebook", "instagram"]
    invalid_platforms = [p for p in request.platforms if p not in supported_platforms]
    
    if invalid_platforms:
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported platforms: {invalid_platforms}. Supported platforms for Day 3: {supported_platforms}"
        )
    
    # Publish to selected platforms
    service = PublishService(db, CURRENT_USER_ID)
    results = await service.publish_to_platforms(
        platforms=request.platforms,
        content=request.content.strip(),
        media_url=request.media_url,
        media_type=request.media_type if request.media_type else None
    )
    
    # Count successful posts
    successful_count = sum(1 for r in results.values() if r.get("success"))
    
    return PublishResponse(
        message="Publishing complete",
        results=results,
        total_platforms=len(request.platforms),
        successful=successful_count
    )


@router.get("/supported-platforms")
async def get_supported_platforms():
    """Get list of currently supported platforms and coming soon."""
    return {
        "current_day": "Day 3",
        "supported_platforms": {
            "facebook": {
                "available": True,
                "features": ["text", "image", "video"],
                "notes": "Posts to user timeline (page support coming soon)"
            },
            "instagram": {
                "available": True,
                "features": ["image", "video"],
                "notes": "Instagram Business accounts only. Text-only posts require image/video."
            }
        },
        "coming_soon": {
            "Day 4": ["twitter", "linkedin"],
            "Day 5": ["youtube", "whatsapp"]
        },
        "how_to_use": {
            "step_1": "Connect to platform: /api/v1/auth/{platform}/connect",
            "step_2": "Check connection: /api/v1/auth/{platform}/tokens",
            "step_3": "Publish: POST /api/v1/publish/ with JSON body"
        },
        "example_curl": 'curl -X POST "http://localhost:8000/api/v1/publish/" -H "Content-Type: application/json" -d \'{"platforms": ["facebook", "instagram"], "content": "Hello from Unified API!", "media_url": "https://picsum.photos/800/600", "media_type": "image"}\''
    }


@router.get("/test")
async def test_publish_endpoint():
    """Simple test endpoint to verify publishing routes are working."""
    return {
        "status": "ready",
        "message": "Publishing endpoints are configured and working!",
        "day": 3,
        "supported_platforms": ["facebook", "instagram"],
        "mock_mode": True,
        "how_to_test": {
            "step_1": "First, connect to a platform: http://localhost:8000/api/v1/auth/facebook/connect",
            "step_2": "Then, publish using POST /api/v1/publish/",
            "step_3": "Check results in the response or at /api/v1/auth/facebook/tokens"
        },
        "quick_start": {
            "connect_facebook": "http://localhost:8000/api/v1/auth/facebook/connect",
            "check_tokens": "http://localhost:8000/api/v1/auth/facebook/tokens",
            "publish_endpoint": "POST http://localhost:8000/api/v1/publish/"
        }
    }


@router.get("/health")
async def publish_health():
    """Health check for publishing service."""
    return {
        "service": "publishing",
        "status": "healthy",
        "adapters_loaded": ["facebook", "instagram"],
        "adapters_pending": ["twitter", "linkedin", "youtube", "whatsapp"],
        "mock_mode_enabled": True,
        "ready_for_production": False,
        "message": "Ready for testing with mock mode. Real credentials will enable actual posting."
    }



@router.get("/posts")
async def get_my_posts(
    db: AsyncSession = Depends(get_db),
    limit: int = 10
):
    """
    Get your recent posts.
    
    Shows all posts you've published with their status.
    """
    service = PublishService(db, CURRENT_USER_ID)
    posts = await service.get_user_posts(limit)
    
    return {
        "total": len(posts),
        "posts": posts
    }


@router.get("/posts/{post_id}")
async def get_post_by_id(
    post_id: int,
    db: AsyncSession = Depends(get_db)
):
    """
    Get a specific post by ID.
    """
    from sqlalchemy import select
    from app.models.post import Post
    
    query = select(Post).where(Post.id == post_id, Post.user_id == CURRENT_USER_ID)
    result = await db.execute(query)
    post = result.scalar_one_or_none()
    
    if not post:
        raise HTTPException(status_code=404, detail="Post not found")
    
    # Get analytics for this post
    from sqlalchemy import select
    from app.models.analytics import AnalyticsRecord
    
    analytics_query = select(AnalyticsRecord).where(AnalyticsRecord.post_id == post_id)
    analytics_result = await db.execute(analytics_query)
    analytics = analytics_result.scalars().all()
    
    return {
        "id": post.id,
        "content": post.content_text,
        "media_url": post.content_media_url,
        "media_type": post.media_type,
        "platforms": post.platforms,
        "status": post.status,
        "created_at": post.created_at.isoformat() if post.created_at else None,
        "published_at": post.published_at.isoformat() if post.published_at else None,
        "analytics": [
            {
                "platform": a.platform,
                "platform_post_id": a.platform_post_id,
                "reach": a.reach,
                "likes": a.likes,
                "comments": a.comments
            }
            for a in analytics
        ]
    }


@router.delete("/posts/{post_id}")
async def delete_post(
    post_id: int,
    db: AsyncSession = Depends(get_db)
):
    """
    Delete a post record (only from database, not from social media).
    """
    from sqlalchemy import select, delete
    from app.models.post import Post
    from app.models.analytics import AnalyticsRecord
    
    # Check if post exists
    query = select(Post).where(Post.id == post_id, Post.user_id == CURRENT_USER_ID)
    result = await db.execute(query)
    post = result.scalar_one_or_none()
    
    if not post:
        raise HTTPException(status_code=404, detail="Post not found")
    
    # Delete analytics first (foreign key constraint)
    await db.execute(delete(AnalyticsRecord).where(AnalyticsRecord.post_id == post_id))
    
    # Delete post
    await db.execute(delete(Post).where(Post.id == post_id))
    
    await db.commit()
    
    return {"message": f"Post {post_id} deleted successfully"}