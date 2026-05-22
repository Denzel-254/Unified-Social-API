"""Facebook Graph API adapter."""

import httpx
from typing import Dict, Any, Optional
from datetime import datetime
from app.adapters.base import BaseAdapter, PostResult, PlatformUser
from app.core.mock_oauth import is_mock_mode
from app.core.config import settings


class FacebookAdapter(BaseAdapter):
    """Adapter for Facebook Graph API."""
    
    BASE_URL = "https://graph.facebook.com"
    API_VERSION = settings.meta_graph_api_version
    
    def __init__(self, access_token: str, page_id: Optional[str] = None):
        """
        Initialize Facebook adapter.
        
        Args:
            access_token: Facebook access token
            page_id: Facebook page ID (if posting as page)
        """
        super().__init__(access_token, "facebook")
        self.page_id = page_id
    
    async def publish_post(
        self,
        content: str,
        media_url: Optional[str] = None,
        media_type: Optional[str] = None
    ) -> PostResult:
        """
        Publish a post to Facebook.
        
        For text-only: Posts to user's timeline or page
        For images: Creates a photo post
        For videos: Creates a video post
        """
        
        # Mock mode for testing
        if is_mock_mode():
            return PostResult(
                success=True,
                platform=self.platform,
                platform_post_id=f"mock_fb_post_{hash(content) % 10000}",
                posted_at=datetime.utcnow(),
                raw_response={
                    "id": f"mock_fb_post_{hash(content) % 10000}",
                    "message": content[:100]
                }
            )
        
        # Real API call
        try:
            async with httpx.AsyncClient() as client:
                if media_url and media_type == "image":
                    # Post photo
                    url = f"{self.BASE_URL}/{self.API_VERSION}/me/photos"
                    data = {
                        "url": media_url,
                        "caption": content,
                        "access_token": self.access_token
                    }
                elif media_url and media_type == "video":
                    # Post video
                    url = f"{self.BASE_URL}/{self.API_VERSION}/me/videos"
                    data = {
                        "url": media_url,
                        "title": content[:100],
                        "description": content,
                        "access_token": self.access_token
                    }
                else:
                    # Text-only post
                    url = f"{self.BASE_URL}/{self.API_VERSION}/me/feed"
                    data = {
                        "message": content,
                        "access_token": self.access_token
                    }
                
                response = await client.post(url, data=data)
                response.raise_for_status()
                result = response.json()
                
                return PostResult(
                    success=True,
                    platform=self.platform,
                    platform_post_id=result.get("id"),
                    posted_at=datetime.utcnow(),
                    raw_response=result
                )
                
        except httpx.HTTPStatusError as e:
            error_detail = e.response.json() if e.response else str(e)
            return PostResult(
                success=False,
                platform=self.platform,
                error_message=f"Facebook API error: {error_detail}"
            )
        except Exception as e:
            return PostResult(
                success=False,
                platform=self.platform,
                error_message=f"Unexpected error: {str(e)}"
            )
    
    async def get_user_info(self) -> PlatformUser:
        """Get Facebook user information."""
        
        if is_mock_mode():
            return PlatformUser(
                platform_user_id="mock_facebook_12345",
                name="Mock Facebook User",
                email="mock_facebook@example.com",
                username="mock_fb_user"
            )
        
        try:
            async with httpx.AsyncClient() as client:
                url = f"{self.BASE_URL}/{self.API_VERSION}/me"
                params = {
                    "access_token": self.access_token,
                    "fields": "id,name,email,username"
                }
                response = await client.get(url, params=params)
                response.raise_for_status()
                data = response.json()
                
                return PlatformUser(
                    platform_user_id=data.get("id"),
                    name=data.get("name"),
                    email=data.get("email"),
                    username=data.get("username")
                )
        except Exception as e:
            print(f"Error getting Facebook user: {e}")
            return PlatformUser(
                platform_user_id="unknown",
                name="Unknown User"
            )
    
    async def check_rate_limit(self) -> Dict:
        """Check Facebook API rate limit status."""
        
        if is_mock_mode():
            return {
                "remaining": 95,
                "limit": 100,
                "reset_time": datetime.utcnow().timestamp() + 3600
            }
        
        try:
            async with httpx.AsyncClient() as client:
                url = f"{self.BASE_URL}/{self.API_VERSION}/me"
                params = {
                    "access_token": self.access_token,
                    "fields": "id"
                }
                response = await client.get(url, params=params)
                
                # Check rate limit headers
                return {
                    "remaining": int(response.headers.get("x-app-usage", {}).get("call_count", 95)),
                    "limit": 100,
                    "reset_time": response.headers.get("x-app-usage-reset", None)
                }
        except Exception:
            return {"remaining": "unknown", "limit": 100}