"""YouTube Data API v3 adapter with resumable upload support."""

import httpx
from typing import Dict, Optional
from datetime import datetime
from app.adapters.base import BaseAdapter, PostResult, PlatformUser
from app.core.mock_oauth import is_mock_mode


class YouTubeAdapter(BaseAdapter):
    """Adapter for YouTube Data API v3."""
    
    BASE_URL = "https://www.googleapis.com/youtube/v3"
    UPLOAD_URL = "https://www.googleapis.com/upload/youtube/v3"
    
    def __init__(self, access_token: str):
        """
        Initialize YouTube adapter.
        
        Args:
            access_token: Google OAuth 2.0 access token
        """
        super().__init__(access_token, "youtube")
    
    async def publish_post(
        self,
        content: str,
        media_url: Optional[str] = None,
        media_type: Optional[str] = None
    ) -> PostResult:
        """
        Upload a video to YouTube.
        
        YouTube requires:
        - Video file (media_url must point to a video file)
        - Title (content[:100])
        - Description (full content)
        - Privacy status (default: unlisted)
        """
        
        # YouTube requires a video file
        if not media_url:
            return PostResult(
                success=False,
                platform=self.platform,
                error_message="YouTube upload requires a video file URL (media_url)"
            )
        
        # Mock mode for testing
        if is_mock_mode():
            return PostResult(
                success=True,
                platform=self.platform,
                platform_post_id=f"mock_yt_video_{hash(media_url) % 10000}",
                posted_at=datetime.utcnow(),
                raw_response={
                    "id": f"mock_yt_video_{hash(media_url) % 10000}",
                    "title": content[:100],
                    "status": "uploaded"
                }
            )
        
        # Real API call - Resumable upload
        try:
            async with httpx.AsyncClient() as client:
                headers = {
                    "Authorization": f"Bearer {self.access_token}",
                    "Content-Type": "application/json"
                }
                
                # Step 1: Initialize upload with metadata
                metadata = {
                    "snippet": {
                        "title": content[:100] if len(content) > 100 else content,
                        "description": content,
                        "tags": ["unified-api", "social-media", "automation"],
                        "categoryId": "22"  # 22 = People & Blogs
                    },
                    "status": {
                        "privacyStatus": "unlisted",  # or "public", "private"
                        "selfDeclaredMadeForKids": False
                    }
                }
                
                # Step 2: Get upload URL
                init_response = await client.post(
                    f"{self.UPLOAD_URL}/videos?part=snippet,status&uploadType=resumable",
                    headers=headers,
                    json=metadata
                )
                init_response.raise_for_status()
                
                # Get upload URL from Location header
                upload_url = init_response.headers.get("Location")
                
                if not upload_url:
                    return PostResult(
                        success=False,
                        platform=self.platform,
                        error_message="Failed to get upload URL"
                    )
                
                # Step 3: Download video from media_url and upload
                async with httpx.AsyncClient() as video_client:
                    video_response = await video_client.get(media_url)
                    video_response.raise_for_status()
                    
                    # Upload video
                    upload_response = await video_client.put(
                        upload_url,
                        content=video_response.content,
                        headers={"Content-Type": "video/*"}
                    )
                    upload_response.raise_for_status()
                    
                    result = upload_response.json()
                    
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
                error_message=f"YouTube API error: {error_detail}"
            )
        except Exception as e:
            return PostResult(
                success=False,
                platform=self.platform,
                error_message=f"Unexpected error: {str(e)}"
            )
    
    async def get_user_info(self) -> PlatformUser:
        """Get YouTube channel information."""
        
        if is_mock_mode():
            return PlatformUser(
                platform_user_id="mock_youtube_33333",
                name="Mock YouTube Channel",
                email="mock_youtube@example.com",
                username="mock_youtube_channel"
            )
        
        try:
            async with httpx.AsyncClient() as client:
                headers = {"Authorization": f"Bearer {self.access_token}"}
                
                response = await client.get(
                    f"{self.BASE_URL}/channels?part=snippet&mine=true",
                    headers=headers
                )
                response.raise_for_status()
                data = response.json()
                
                if data.get("items"):
                    channel = data["items"][0]
                    snippet = channel.get("snippet", {})
                    return PlatformUser(
                        platform_user_id=channel.get("id"),
                        name=snippet.get("title"),
                        email=snippet.get("customUrl", ""),
                        username=snippet.get("customUrl", "")
                    )
                
                return PlatformUser(
                    platform_user_id="unknown",
                    name="Unknown Channel"
                )
        except Exception as e:
            print(f"Error getting YouTube channel: {e}")
            return PlatformUser(
                platform_user_id="unknown",
                name="Unknown User"
            )
    
    async def check_rate_limit(self) -> Dict:
        """Check YouTube API quota usage."""
        
        if is_mock_mode():
            return {
                "remaining": 9500,
                "limit": 10000,
                "unit": "quota points per day"
            }
        
        # YouTube uses quota system (10,000 points/day)
        # Each upload costs ~1600 points
        return {"remaining": "check Google Cloud Console", "limit": 10000}
    
    async def get_video_comments(self, video_id: str) -> list:
        """Get comments for a video."""
        
        if is_mock_mode():
            return [
                {
                    "id": f"mock_comment_{i}",
                    "text": f"Mock comment {i + 1}",
                    "author": "Mock Viewer",
                    "like_count": i * 10,
                    "published_at": datetime.utcnow().isoformat()
                }
                for i in range(3)
            ]
        
        try:
            async with httpx.AsyncClient() as client:
                headers = {"Authorization": f"Bearer {self.access_token}"}
                
                response = await client.get(
                    f"{self.BASE_URL}/commentThreads?part=snippet&videoId={video_id}&maxResults=50",
                    headers=headers
                )
                response.raise_for_status()
                data = response.json()
                
                comments = []
                for item in data.get("items", []):
                    snippet = item.get("snippet", {}).get("topLevelComment", {}).get("snippet", {})
                    comments.append({
                        "id": item.get("id"),
                        "text": snippet.get("textDisplay", ""),
                        "author": snippet.get("authorDisplayName", ""),
                        "like_count": snippet.get("likeCount", 0),
                        "published_at": snippet.get("publishedAt", "")
                    })
                
                return comments
        except Exception as e:
            print(f"Error getting comments: {e}")
            return []