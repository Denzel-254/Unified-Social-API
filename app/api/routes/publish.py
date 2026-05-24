"""Publishing endpoints - Day 4: Twitter & LinkedIn Integration."""

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc, delete
from sqlalchemy import cast, String
from app.core.database import get_db
from app.services.publish_service import PublishService
from app.services.token_service import TokenService
from app.adapters.twitter import TwitterAdapter
from app.models.post import Post
from app.models.analytics import AnalyticsRecord
from app.tasks.publish_tasks import publish_to_platforms_task, check_publish_status
from fastapi import BackgroundTasks
import uuid
from datetime import datetime


router = APIRouter(prefix="/publish", tags=["publishing"])

# Temporary user ID (will be replaced with real auth in later days)
CURRENT_USER_ID = 1

_task_store = {}



class PublishRequest(BaseModel):
    """Request model for publishing content to platforms."""
    platforms: List[str] 
    content: str
    media_url: Optional[str] = None
    media_type: Optional[str] = None


class PublishResponse(BaseModel):
    """Response model for publishing results."""
    message: str
    results: dict
    total_platforms: int
    successful: int


class ThreadRequest(BaseModel):
    """Request model for posting a Twitter thread."""
    tweets: List[str]


class AsyncPublishRequest(BaseModel):
    """Request model for async publishing."""
    platforms: List[str]
    content: str
    media_url: Optional[str] = None
    media_type: Optional[str] = None


@router.post("/", response_model=PublishResponse)
async def publish_content(
    request: PublishRequest,
    db: AsyncSession = Depends(get_db)
):
    """Publish content to selected platforms."""
    
    if not request.platforms:
        raise HTTPException(status_code=400, detail="At least one platform must be specified.")
    
    if not request.content or len(request.content.strip()) == 0:
        raise HTTPException(status_code=400, detail="Content cannot be empty.")
    
    if request.media_url:
        if not request.media_type:
            raise HTTPException(status_code=400, detail="media_type is required when media_url is provided.")
        if request.media_type not in ["image", "video"]:
            raise HTTPException(status_code=400, detail="media_type must be 'image' or 'video'.")
    
    supported_platforms = ["facebook", "instagram", "twitter", "linkedin", "youtube", "whatsapp"]
    invalid_platforms = [p for p in request.platforms if p not in supported_platforms]
    
    if invalid_platforms:
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported platforms: {invalid_platforms}. Supported platforms: {supported_platforms}"
        )
    
    service = PublishService(db, CURRENT_USER_ID)
    results = await service.publish_to_platforms(
        platforms=request.platforms,
        content=request.content.strip(),
        media_url=request.media_url,
        media_type=request.media_type if request.media_type else None
    )
    
    successful_count = sum(1 for r in results.values() if r.get("success"))
    
    return PublishResponse(
        message="Publishing complete",
        results=results,
        total_platforms=len(request.platforms),
        successful=successful_count
    )




@router.post("/async")
async def publish_async(
    request: AsyncPublishRequest,
    db: AsyncSession = Depends(get_db)
):
    """
    Publish content asynchronously (recommended for multiple platforms).
    
    This returns immediately with a task ID. Use GET /publish/status/{task_id}
    to check progress and results.
    """
    # Validate platforms
    supported_platforms = ["facebook", "instagram", "twitter", "linkedin", "youtube", "whatsapp"]
    invalid = [p for p in request.platforms if p not in supported_platforms]

    if not request.platforms:
        raise HTTPException(status_code=400, detail="At least one platform must be specified.")
    
    if invalid:
        raise HTTPException(status_code=400, detail=f"Unsupported platforms: {invalid}")
    
    # Validate content
    if not request.content or len(request.content.strip()) == 0:
        raise HTTPException(status_code=400, detail="Content cannot be empty.")
    
    # Validate media
    if request.media_url and not request.media_type:
        raise HTTPException(status_code=400, detail="media_type is required when media_url is provided.")
    
    # Start async task
    task = publish_to_platforms_task.delay(
        user_id=CURRENT_USER_ID,
        platforms=request.platforms,
        content=request.content.strip(),
        media_url=request.media_url,
        media_type=request.media_type
    )
    
    return {
        "message": "Publish task submitted successfully",
        "task_id": task.id,
        "status": "processing",
        "check_status_url": f"/api/v1/publish/status/{task.id}",
        "platforms": request.platforms,
        "estimated_time": f"~{len(request.platforms) * 2} seconds"
    }


@router.get("/status/{task_id}")
async def get_publish_status(task_id: str):
    """
    Get the status of an async publish task.
    
    Status values:
    - PENDING: Task waiting to start
    - STARTED: Task is processing
    - PUBLISHING: Currently publishing to platforms
    - SUCCESS: Completed successfully
    - FAILURE: Failed (check error)
    """
    result = check_publish_status(task_id)
    
    return {
        "task_id": task_id,
        "status": result["status"],
        "is_complete": result["ready"],
        "is_successful": result.get("successful"),
        "details": result.get("result") if result.get("ready") else result.get("info"),
        "check_again": f"/api/v1/publish/status/{task_id}" if not result["ready"] else None
    }


@router.post("/retry-failed")
async def retry_failed_posts():
    """
    Retry all failed posts from the database.
    
    This is useful for recovering from temporary API issues.
    """
    from app.tasks.publish_tasks import retry_failed_posts
    
    result = await retry_failed_posts(user_id=CURRENT_USER_ID)
    
    return result




@router.post("/thread")
async def post_twitter_thread(
    request: ThreadRequest,
    db: AsyncSession = Depends(get_db)
):
    """
    Post a Twitter thread (multiple tweets in sequence) and save to database.
    
    Example request:
    {
        "tweets": [
            "Thread part 1: This is my first tweet!",
            "Thread part 2: Continuing the conversation...",
            "Thread part 3: Thanks for reading!"
        ]
    }
    """
    
    # Validate request
    if not request.tweets:
        raise HTTPException(status_code=400, detail="At least one tweet is required")
    
    if len(request.tweets) > 25:
        raise HTTPException(status_code=400, detail="Maximum 25 tweets per thread")
    
    # Check each tweet length
    for i, tweet in enumerate(request.tweets):
        if len(tweet) > 280:
            raise HTTPException(
                status_code=400,
                detail=f"Tweet {i+1} exceeds 280 character limit (current: {len(tweet)})"
            )
    
    # Check if user has Twitter token
    token = await TokenService.get_token(db, CURRENT_USER_ID, "twitter")
    
    if not token:
        raise HTTPException(status_code=401, detail="Twitter not connected. Please connect first: /api/v1/auth/twitter/connect")
    
    # Create a post record for the thread
    post = Post(
        user_id=CURRENT_USER_ID,
        content_text=f"Twitter Thread ({len(request.tweets)} tweets): {request.tweets[0][:50]}...",
        content_media_url=None,
        media_type=None,
        platforms=["twitter"],
        status="processing",
        created_at=datetime.utcnow()
    )
    db.add(post)
    await db.commit()
    await db.refresh(post)
    
    print(f"Created thread post record #{post.id} for Twitter thread")
    
    # Create adapter and post thread
    adapter = TwitterAdapter(token.access_token)
    results = await adapter.post_thread(request.tweets)
    
    # Save each tweet as analytics record
    successful_tweets = []
    failed_tweets = []
    
    for i, result in enumerate(results):
        if result.success and result.platform_post_id:
            analytics = AnalyticsRecord(
                post_id=post.id,
                platform="twitter",
                platform_post_id=result.platform_post_id,
                collected_at=datetime.utcnow()
            )
            db.add(analytics)
            successful_tweets.append({
                "tweet_number": i + 1,
                "tweet_id": result.platform_post_id,
                "content": request.tweets[i][:100]
            })
        else:
            failed_tweets.append({
                "tweet_number": i + 1,
                "error": result.error_message,
                "content": request.tweets[i][:100]
            })
    
    # Update post status
    if len(successful_tweets) == len(results):
        post.status = "completed"
    elif successful_tweets:
        post.status = "partial"
    else:
        post.status = "failed"
    
    post.published_at = datetime.utcnow()
    await db.commit()
    
    print(f"Thread post #{post.id} status: {post.status} ({len(successful_tweets)}/{len(results)} successful)")
    
    return {
        "message": f"Posted {len(results)} tweets",
        "post_id": post.id,
        "thread_id": f"thread_{post.id}_{hash(str(request.tweets))}",
        "results": [
            {
                "tweet_number": i + 1,
                "success": r.success,
                "tweet_id": r.platform_post_id,
                "tweet_text": request.tweets[i][:50] + ("..." if len(request.tweets[i]) > 50 else ""),
                "error": r.error_message
            }
            for i, r in enumerate(results)
        ],
        "successful_count": len(successful_tweets),
        "failed_count": len(failed_tweets),
        "saved_to_database": True,
        "database_post_id": post.id
    }


@router.get("/threads")
async def get_my_threads(
    db: AsyncSession = Depends(get_db),
    limit: int = 10
):
    """
    Get all your Twitter threads from the database.
    
    Shows threads with their individual tweets/analytics.
    """
    # Get all posts first
    query = select(Post).where(
        Post.user_id == CURRENT_USER_ID
    ).order_by(desc(Post.created_at)).limit(limit)
    
    result = await db.execute(query)
    posts = result.scalars().all()
    
    threads = []
    for post in posts:
        # Check if post is a Twitter thread (platforms list contains "twitter")
        if "twitter" in post.platforms:
            # Get all tweets in this thread
            analytics_query = select(AnalyticsRecord).where(AnalyticsRecord.post_id == post.id)
            analytics_result = await db.execute(analytics_query)
            tweets = analytics_result.scalars().all()
            
            threads.append({
                "thread_id": post.id,
                "created_at": post.created_at.isoformat() if post.created_at else None,
                "published_at": post.published_at.isoformat() if post.published_at else None,
                "status": post.status,
                "tweet_count": len(tweets),
                "tweets": [
                    {
                        "tweet_number": i + 1,
                        "tweet_id": t.platform_post_id,
                        "collected_at": t.collected_at.isoformat() if t.collected_at else None
                    }
                    for i, t in enumerate(tweets)
                ],
                "preview": post.content_text[:100] if post.content_text else ""
            })
    
    return {
        "total_threads": len(threads),
        "threads": threads
    }


@router.get("/threads/{thread_id}")
async def get_thread_by_id(
    thread_id: int,
    db: AsyncSession = Depends(get_db)
):
    """
    Get a specific thread by ID with all its tweets.
    """
    query = select(Post).where(Post.id == thread_id, Post.user_id == CURRENT_USER_ID)
    result = await db.execute(query)
    post = result.scalar_one_or_none()
    
    if not post:
        raise HTTPException(status_code=404, detail="Thread not found")
    
    analytics_query = select(AnalyticsRecord).where(AnalyticsRecord.post_id == thread_id)
    analytics_result = await db.execute(analytics_query)
    tweets = analytics_result.scalars().all()
    
    return {
        "thread_id": post.id,
        "status": post.status,
        "created_at": post.created_at.isoformat() if post.created_at else None,
        "published_at": post.published_at.isoformat() if post.published_at else None,
        "tweet_count": len(tweets),
        "tweets": [
            {
                "tweet_number": i + 1,
                "tweet_id": t.platform_post_id,
                "created_at": t.collected_at.isoformat() if t.collected_at else None,
                "analytics": {
                    "reach": t.reach,
                    "likes": t.likes,
                    "comments": t.comments,
                    "shares": t.shares
                }
            }
            for i, t in enumerate(tweets)
        ]
    }


@router.get("/posts")
async def get_my_posts(
    db: AsyncSession = Depends(get_db),
    limit: int = 10
):
    """Get your recent posts from database."""
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
    """Get a specific post by ID with analytics."""
    query = select(Post).where(Post.id == post_id, Post.user_id == CURRENT_USER_ID)
    result = await db.execute(query)
    post = result.scalar_one_or_none()
    
    if not post:
        raise HTTPException(status_code=404, detail="Post not found")
    
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
    """Delete a post record from database (not from social media)."""
    query = select(Post).where(Post.id == post_id, Post.user_id == CURRENT_USER_ID)
    result = await db.execute(query)
    post = result.scalar_one_or_none()
    
    if not post:
        raise HTTPException(status_code=404, detail="Post not found")
    
    await db.execute(delete(AnalyticsRecord).where(AnalyticsRecord.post_id == post_id))
    await db.execute(delete(Post).where(Post.id == post_id))
    await db.commit()
    
    return {"message": f"Post {post_id} deleted successfully"}



@router.get("/supported-platforms")
async def get_supported_platforms():
    return {
        "current_day": "Day 6 - Async Publishing Added!",
        "supported_platforms": {
            "facebook": {"available": True, "features": ["text", "image", "video"]},
            "instagram": {"available": True, "features": ["image", "video"]},
            "twitter": {"available": True, "features": ["text", "threads", "replies"]},
            "linkedin": {"available": True, "features": ["text", "image"]},
            "youtube": {"available": True, "features": ["video upload"], "notes": "Requires video URL"},
            "whatsapp": {"available": True, "features": ["text", "image", "video"], "notes": "Business API only"}
        },
        "async_publishing": {
            "available": True,
            "endpoint": "POST /api/v1/publish/async",
            "status_endpoint": "GET /api/v1/publish/status/{task_id}",
            "benefits": "No waiting - API returns instantly, tasks run in background"
        },
        "total_platforms": 6,
        "message": "ALL 6 PLATFORMS + ASYNC PUBLISHING!"
    }

@router.get("/health")
async def publish_health():
    """Health check for publishing service."""
    return {
        "service": "publishing",
        "status": "healthy",
        "adapters_loaded": ["facebook", "instagram", "twitter", "linkedin", "youtube", "whatsapp"],
        "async_enabled": True,
        "mock_mode_enabled": True,
        "ready_for_production": False,
        "message": "All 6 platforms ready! Use /async for non-blocking publishing."
    }


@router.post("/background")
async def publish_background(
    request: AsyncPublishRequest,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db)
):
    """
    Publish content in the background using FastAPI BackgroundTasks.
    
    This returns immediately with a task ID. Use GET /publish/background/status/{task_id}
    to check progress.
    """
    # Validate platforms
    supported_platforms = ["facebook", "instagram", "twitter", "linkedin", "youtube", "whatsapp"]
    invalid = [p for p in request.platforms if p not in supported_platforms]
    
    if invalid:
        raise HTTPException(status_code=400, detail=f"Unsupported platforms: {invalid}")
    
    # Validate content
    if not request.content or len(request.content.strip()) == 0:
        raise HTTPException(status_code=400, detail="Content cannot be empty.")
    
    # Generate a task ID
    task_id = str(uuid.uuid4())
    
    # Store task info
    _task_store[task_id] = {
        "status": "pending",
        "platforms": request.platforms,
        "created_at": datetime.utcnow().isoformat()
    }
    
    # Add background task
    background_tasks.add_task(
        run_background_publish,
        task_id=task_id,
        user_id=CURRENT_USER_ID,
        platforms=request.platforms,
        content=request.content.strip(),
        media_url=request.media_url,
        media_type=request.media_type
    )
    
    return {
        "message": "Publish task submitted successfully",
        "task_id": task_id,
        "status": "pending",
        "check_status_url": f"/api/v1/publish/background/status/{task_id}",
        "platforms": request.platforms
    }


@router.get("/background/status/{task_id}")
async def get_background_status(task_id: str):
    """Get the status of a background task."""
    
    task = _task_store.get(task_id)
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    
    return {
        "task_id": task_id,
        "status": task.get("status", "unknown"),
        "result": task.get("result"),
        "error": task.get("error"),
        "platforms": task.get("platforms"),
        "created_at": task.get("created_at"),
        "completed_at": task.get("completed_at")
    }


async def run_background_publish(
    task_id: str,
    user_id: int,
    platforms: List[str],
    content: str,
    media_url: Optional[str] = None,
    media_type: Optional[str] = None
):
    """Background task to publish content."""
    
    from app.services.publish_service import PublishService
    from app.core.database import AsyncSessionLocal
    
    # Update status to running
    _task_store[task_id]["status"] = "running"
    
    try:
        async with AsyncSessionLocal() as db:
            service = PublishService(db, user_id)
            results = await service.publish_to_platforms(
                platforms=platforms,
                content=content,
                media_url=media_url,
                media_type=media_type
            )
            
            successful = sum(1 for r in results.values() if r.get("success"))
            
            # Update task store with results
            _task_store[task_id].update({
                "status": "completed",
                "result": results,
                "successful": successful,
                "total": len(platforms),
                "completed_at": datetime.utcnow().isoformat()
            })
            
            print(f"Background task {task_id}: Published to {successful}/{len(platforms)} platforms")
            
    except Exception as e:
        _task_store[task_id].update({
            "status": "failed",
            "error": str(e),
            "completed_at": datetime.utcnow().isoformat()
        })
        print(f"Background task {task_id} failed: {e}")