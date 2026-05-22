"""Unified publish service - routes content to platform adapters and saves to database."""

from typing import List, Dict, Any, Optional
from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession
from app.services.token_service import TokenService
from app.adapters.facebook import FacebookAdapter
from app.adapters.instagram import InstagramAdapter
from app.adapters.twitter import TwitterAdapter
from app.adapters.linkedin import LinkedInAdapter
from app.core.mock_oauth import is_mock_mode
from app.models.post import Post
from app.models.analytics import AnalyticsRecord


class PublishService:
    """Service for publishing content to multiple platforms."""
    
    def __init__(self, db: AsyncSession, user_id: int):
        self.db = db
        self.user_id = user_id
    
    async def publish_to_platforms(
        self,
        platforms: List[str],
        content: str,
        media_url: Optional[str] = None,
        media_type: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Publish content to selected platforms and save to database.
        
        Returns:
            Dictionary with results for each platform
        """
        
        # Step 1: Create a post record in the database
        post = Post(
            user_id=self.user_id,
            content_text=content,
            content_media_url=media_url,
            media_type=media_type,
            platforms=platforms,
            status="processing",
            created_at=datetime.utcnow()
        )
        self.db.add(post)
        await self.db.commit()
        await self.db.refresh(post)
        
        print(f" Created post record #{post.id} for platforms: {platforms}")
        
        results = {}
        all_successful = True
        
        for platform in platforms:
            try:
                # Get token for this platform
                token = await TokenService.get_token(self.db, self.user_id, platform)
                
                if not token:
                    results[platform] = {
                        "success": False,
                        "error": f"No token found for {platform}. Please connect this platform first."
                    }
                    all_successful = False
                    continue
                
                # Create appropriate adapter
                adapter = await self._create_adapter(platform, token.access_token)
                
                if not adapter:
                    results[platform] = {
                        "success": False,
                        "error": f"Platform '{platform}' not supported yet."
                    }
                    all_successful = False
                    continue
                
                # Publish the content
                result = await adapter.publish_post(content, media_url, media_type)
                
                # Save platform-specific post ID to analytics
                if result.success and result.platform_post_id:
                    analytics = AnalyticsRecord(
                        post_id=post.id,
                        platform=platform,
                        platform_post_id=result.platform_post_id,
                        collected_at=datetime.utcnow()
                    )
                    self.db.add(analytics)
                    await self.db.commit()
                
                results[platform] = {
                    "success": result.success,
                    "platform_post_id": result.platform_post_id,
                    "error": result.error_message if not result.success else None,
                    "posted_at": result.posted_at.isoformat() if result.posted_at else None
                }
                
                if not result.success:
                    all_successful = False
                
            except Exception as e:
                results[platform] = {
                    "success": False,
                    "error": f"Unexpected error: {str(e)}"
                }
                all_successful = False
        
        # Update post status based on results
        if all_successful:
            post.status = "completed"
        elif any(r.get("success") for r in results.values()):
            post.status = "partial"
        else:
            post.status = "failed"
        
        post.published_at = datetime.utcnow()
        await self.db.commit()
        
        print(f"Post #{post.id} status: {post.status}")
        
        return results
    
    async def _create_adapter(self, platform: str, access_token: str):
        """Create the appropriate adapter for a platform."""
        
        if platform == "facebook":
            return FacebookAdapter(access_token)
        elif platform == "instagram":
            # For Instagram, we need the business ID from the token
            token = await TokenService.get_token(self.db, self.user_id, platform)
            instagram_business_id = token.platform_user_id if token else None
            
            if not instagram_business_id and is_mock_mode():
                instagram_business_id = "mock_instagram_business_id"
            
            return InstagramAdapter(access_token, instagram_business_id or "unknown")
        elif platform == "twitter":
            return TwitterAdapter(access_token)
        elif platform == "linkedin":
            return LinkedInAdapter(access_token)
        else:
            return None
    
    async def get_user_posts(self, limit: int = 10) -> List[Dict]:
        """Get recent posts for the user."""
        
        from sqlalchemy import select, desc
        
        query = select(Post).where(Post.user_id == self.user_id).order_by(desc(Post.created_at)).limit(limit)
        result = await self.db.execute(query)
        posts = result.scalars().all()
        
        return [
            {
                "id": p.id,
                "content": p.content_text,
                "media_url": p.content_media_url,
                "media_type": p.media_type,
                "platforms": p.platforms,
                "status": p.status,
                "created_at": p.created_at.isoformat() if p.created_at else None,
                "published_at": p.published_at.isoformat() if p.published_at else None
            }
            for p in posts
        ]