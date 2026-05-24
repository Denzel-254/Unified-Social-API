"""Celery tasks for async publishing - with fallback for development."""

from typing import List, Optional, Dict, Any
from datetime import datetime
from app.core.celery_app import celery_app


@celery_app.task(bind=True, name="publish_to_platforms")
def publish_to_platforms_task(
    self,
    user_id: int,
    platforms: List[str],
    content: str,
    media_url: Optional[str] = None,
    media_type: Optional[str] = None
) -> Dict[str, Any]:
    """
    Publish content to multiple platforms (synchronous fallback for dev).
    
    In development without Redis, this runs synchronously.
    In production with Redis, this runs asynchronously.
    """
    import asyncio
    from app.services.publish_service import PublishService
    from app.core.database import AsyncSessionLocal
    from app.models.post import Post
    
    print(f"📝 Task {self.request.id}: Starting publish to {platforms}")
    
    # Run async code in sync context
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    
    try:
        async def _run():
            async with AsyncSessionLocal() as db:
                # Create post record
                post = Post(
                    user_id=user_id,
                    content_text=content,
                    content_media_url=media_url,
                    media_type=media_type,
                    platforms=platforms,
                    status="processing",
                    created_at=datetime.utcnow()
                )
                db.add(post)
                await db.commit()
                await db.refresh(post)
                
                # Publish to platforms
                service = PublishService(db, user_id)
                results = await service.publish_to_platforms(
                    platforms=platforms,
                    content=content,
                    media_url=media_url,
                    media_type=media_type
                )
                
                # Update post status
                successful = sum(1 for r in results.values() if r.get("success"))
                if successful == len(platforms):
                    post.status = "completed"
                elif successful > 0:
                    post.status = "partial"
                else:
                    post.status = "failed"
                
                post.published_at = datetime.utcnow()
                await db.commit()
                
                return {
                    "task_id": self.request.id,
                    "post_id": post.id,
                    "status": "completed",
                    "results": results,
                    "successful": successful,
                    "total": len(platforms),
                    "completed_at": datetime.utcnow().isoformat()
                }
        
        result = loop.run_until_complete(_run())
        return result
        
    except Exception as e:
        self.update_state(state="FAILURE", meta={"error": str(e)})
        raise
    finally:
        loop.close()


@celery_app.task(name="check_publish_status")
def check_publish_status(task_id: str) -> Dict[str, Any]:
    """Check the status of a publish task."""
    from celery.result import AsyncResult
    
    result = AsyncResult(task_id, app=celery_app)
    
    response = {
        "task_id": task_id,
        "status": result.status,
        "ready": result.ready(),
        "successful": result.successful() if result.ready() else None,
    }
    
    if result.ready():
        if result.successful():
            response["result"] = result.result
        else:
            response["error"] = str(result.info)
    else:
        response["info"] = result.info
    
    return response


@celery_app.task(name="retry_failed_posts")
def retry_failed_posts(user_id: int = None) -> Dict[str, Any]:
    """Retry failed posts from the database."""
    import asyncio
    from app.core.database import AsyncSessionLocal
    from sqlalchemy import select
    from app.models.post import Post
    
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    
    try:
        async def _run():
            async with AsyncSessionLocal() as db:
                query = select(Post).where(Post.status == "failed")
                if user_id:
                    query = query.where(Post.user_id == user_id)
                
                result = await db.execute(query)
                failed_posts = result.scalars().all()
                
                retry_results = []
                for post in failed_posts:
                    task = publish_to_platforms_task.delay(
                        user_id=post.user_id,
                        platforms=post.platforms,
                        content=post.content_text,
                        media_url=post.content_media_url,
                        media_type=post.media_type
                    )
                    retry_results.append({
                        "post_id": post.id,
                        "task_id": task.id,
                        "platforms": post.platforms
                    })
                
                return {
                    "message": f"Retrying {len(failed_posts)} failed posts",
                    "retried_posts": retry_results
                }
        
        return loop.run_until_complete(_run())
    finally:
        loop.close()