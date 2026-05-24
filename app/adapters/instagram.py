"""Instagram Graph API adapter."""

import httpx
from typing import Dict, Optional
from datetime import datetime
from app.adapters.base import BaseAdapter, PostResult, PlatformUser
from app.core.mock_oauth import is_mock_mode
from app.core.config import settings


class InstagramAdapter(BaseAdapter):
    """Adapter for Instagram Graph API."""
    
    BASE_URL = "https://graph.facebook.com"
    API_VERSION = settings.meta_graph_api_version
    
    def __init__(self, access_token: str, instagram_business_id: str):
        """
        Initialize Instagram adapter.
        
        Args:
            access_token: Facebook access token (with Instagram permissions)
            instagram_business_id: Instagram Business Account ID
        """
        super().__init__(access_token, "instagram")
        self.instagram_business_id = instagram_business_id
    
    async def publish_post(
        self,
        content: str,
        media_url: Optional[str] = None,
        media_type: Optional[str] = None
    ) -> PostResult:
        """
        Publish to Instagram Business Account.
        
        Instagram requires a two-step process:
        1. Create media container
        2. Publish the container
        """
        
        if is_mock_mode():
            return PostResult(
                success=True,
                platform=self.platform,
                platform_post_id=f"mock_ig_post_{hash(content) % 10000}",
                posted_at=datetime.utcnow(),
                raw_response={
                    "id": f"mock_ig_post_{hash(content) % 10000}",
                    "media_type": media_type or "TEXT"
                }
            )
        
        try:
            async with httpx.AsyncClient() as client:
                # Step 1: Create media container
                if media_url and media_type == "image":
                    container_url = f"{self.BASE_URL}/{self.API_VERSION}/{self.instagram_business_id}/media"
                    container_data = {
                        "image_url": media_url,
                        "caption": content,
                        "access_token": self.access_token
                    }
                elif media_url and media_type == "video":
                    container_url = f"{self.BASE_URL}/{self.API_VERSION}/{self.instagram_business_id}/media"
                    container_data = {
                        "video_url": media_url,
                        "caption": content,
                        "media_type": "VIDEO",
                        "access_token": self.access_token
                    }
                else:
                    # Text-only? Instagram requires image/video for business accounts
                    return PostResult(
                        success=False,
                        platform=self.platform,
                        error_message="Instagram business posts require an image or video"
                    )
                
                # Create container
                response = await client.post(container_url, data=container_data)
                response.raise_for_status()
                container_id = response.json().get("id")
                
                # Step 2: Publish the container
                publish_url = f"{self.BASE_URL}/{self.API_VERSION}/{self.instagram_business_id}/media_publish"
                publish_data = {
                    "creation_id": container_id,
                    "access_token": self.access_token
                }
                
                publish_response = await client.post(publish_url, data=publish_data)
                publish_response.raise_for_status()
                result = publish_response.json()
                
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
                error_message=f"Instagram API error: {error_detail}"
            )
        except Exception as e:
            return PostResult(
                success=False,
                platform=self.platform,
                error_message=f"Unexpected error: {str(e)}"
            )
    
    async def get_user_info(self) -> PlatformUser:
        """Get Instagram Business Account info."""
        
        if is_mock_mode():
            return PlatformUser(
                platform_user_id="mock_instagram_67890",
                name="Mock Instagram Business",
                username="mock_ig_business"
            )
        
        try:
            async with httpx.AsyncClient() as client:
                url = f"{self.BASE_URL}/{self.API_VERSION}/{self.instagram_business_id}"
                params = {
                    "access_token": self.access_token,
                    "fields": "id,username,name"
                }
                response = await client.get(url, params=params)
                response.raise_for_status()
                data = response.json()
                
                return PlatformUser(
                    platform_user_id=data.get("id"),
                    name=data.get("name"),
                    username=data.get("username")
                )
        except Exception as e:
            print(f"Error getting Instagram user: {e}")
            return PlatformUser(
                platform_user_id="unknown",
                name="Unknown User"
            )
    
    async def check_rate_limit(self) -> Dict:
        """Check Instagram API rate limits."""
        
        if is_mock_mode():
            return {
                "remaining": 4500,
                "limit": 5000,
                "reset_time": datetime.utcnow().timestamp() + 3600
            }
        
        return {"remaining": "unknown", "limit": 5000}