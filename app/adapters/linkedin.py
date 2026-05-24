"""LinkedIn API v2 adapter."""

import httpx
from typing import Dict, Optional
from datetime import datetime
from app.adapters.base import BaseAdapter, PostResult, PlatformUser
from app.core.mock_oauth import is_mock_mode


class LinkedInAdapter(BaseAdapter):
    """Adapter for LinkedIn API v2."""
    
    BASE_URL = "https://api.linkedin.com/v2"
    
    def __init__(self, access_token: str, author_id: str = None):
        """
        Initialize LinkedIn adapter.
        
        Args:
            access_token: LinkedIn OAuth 2.0 access token
            author_id: LinkedIn user/company ID (if None, gets from API)
        """
        super().__init__(access_token, "linkedin")
        self.author_id = author_id
    
    async def publish_post(
        self,
        content: str,
        media_url: Optional[str] = None,
        media_type: Optional[str] = None
    ) -> PostResult:
        """
        Publish a post to LinkedIn.
        
        LinkedIn supports:
        - Text-only posts (shares)
        - Image posts (with media upload)
        """
        
        # Get author ID if not provided
        if not self.author_id:
            user_info = await self.get_user_info()
            self.author_id = user_info.platform_user_id
        
        # Mock mode for testing
        if is_mock_mode():
            return PostResult(
                success=True,
                platform=self.platform,
                platform_post_id=f"mock_li_post_{hash(content) % 10000}",
                posted_at=datetime.utcnow(),
                raw_response={
                    "id": f"mock_li_post_{hash(content) % 10000}",
                    "activity": f"urn:li:activity:mock_{hash(content) % 10000}"
                }
            )
        
        # Real API call
        try:
            async with httpx.AsyncClient() as client:
                headers = {
                    "Authorization": f"Bearer {self.access_token}",
                    "Content-Type": "application/json",
                    "X-Restli-Protocol-Version": "2.0.0"
                }
                
                if media_url and media_type == "image":
                    # First, register the image upload
                    # Register upload
                    register_url = f"{self.BASE_URL}/assets?action=registerUpload"
                    register_data = {
                        "registerUploadRequest": {
                            "recipes": ["urn:li:digitalmediaRecipe:feedshare-image"],
                            "owner": f"urn:li:person:{self.author_id}",
                            "serviceRelationships": [
                                {
                                    "relationshipType": "OWNER",
                                    "identifier": "urn:li:userGeneratedContent"
                                }
                            ]
                        }
                    }
                    
                    register_response = await client.post(register_url, headers=headers, json=register_data)
                    register_response.raise_for_status()
                    upload_url = register_response.json().get("value", {}).get("uploadMechanism", {}).get(
                        "com.linkedin.digitalmedia.uploading.MediaUploadHttpRequest", {}
                    ).get("uploadUrl")
                    
                    # Upload image
                    if upload_url:
                        async with httpx.AsyncClient() as media_client:
                            media_response = await media_client.get(media_url)
                            upload_response = await media_client.put(upload_url, content=media_response.content)
                            upload_response.raise_for_status()
                    
                    asset_id = register_response.json().get("value", {}).get("asset")
                    
                    # Create post with image
                    post_data = {
                        "author": f"urn:li:person:{self.author_id}",
                        "lifecycleState": "PUBLISHED",
                        "specificContent": {
                            "com.linkedin.ugc.ShareContent": {
                                "shareCommentary": {
                                    "text": content
                                },
                                "shareMediaCategory": "IMAGE",
                                "media": [
                                    {
                                        "status": "READY",
                                        "description": {
                                            "text": content[:100]
                                        },
                                        "media": asset_id,
                                        "title": {
                                            "text": content[:50]
                                        }
                                    }
                                ]
                            }
                        },
                        "visibility": {
                            "com.linkedin.ugc.MemberNetworkVisibility": "PUBLIC"
                        }
                    }
                else:
                    # Text-only post
                    post_data = {
                        "author": f"urn:li:person:{self.author_id}",
                        "lifecycleState": "PUBLISHED",
                        "specificContent": {
                            "com.linkedin.ugc.ShareContent": {
                                "shareCommentary": {
                                    "text": content
                                },
                                "shareMediaCategory": "NONE"
                            }
                        },
                        "visibility": {
                            "com.linkedin.ugc.MemberNetworkVisibility": "PUBLIC"
                        }
                    }
                
                response = await client.post(
                    f"{self.BASE_URL}/ugcPosts",
                    headers=headers,
                    json=post_data
                )
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
                error_message=f"LinkedIn API error: {error_detail}"
            )
        except Exception as e:
            return PostResult(
                success=False,
                platform=self.platform,
                error_message=f"Unexpected error: {str(e)}"
            )
    
    async def get_user_info(self) -> PlatformUser:
        """Get LinkedIn user information."""
        
        if is_mock_mode():
            return PlatformUser(
                platform_user_id="mock_linkedin_22222",
                name="Mock LinkedIn User",
                email="mock_linkedin@example.com",
                username="mock_linkedin_user"
            )
        
        try:
            async with httpx.AsyncClient() as client:
                headers = {"Authorization": f"Bearer {self.access_token}"}
                
                response = await client.get(
                    f"{self.BASE_URL}/userinfo",
                    headers=headers
                )
                response.raise_for_status()
                data = response.json()
                
                return PlatformUser(
                    platform_user_id=data.get("sub"),
                    name=data.get("name"),
                    email=data.get("email")
                )
        except Exception as e:
            print(f"Error getting LinkedIn user: {e}")
            return PlatformUser(
                platform_user_id="unknown",
                name="Unknown User"
            )
    
    async def check_rate_limit(self) -> Dict:
        """Check LinkedIn API rate limits."""
        
        if is_mock_mode():
            return {
                "remaining": 95,
                "limit": 100,
                "reset_time": datetime.utcnow().timestamp() + 3600
            }
        
        return {"remaining": "check headers", "limit": 100}