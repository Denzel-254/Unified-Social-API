"""Twitter/X API v2 adapter."""

import httpx
from typing import Dict, Optional
from datetime import datetime
from app.adapters.base import BaseAdapter, PostResult, PlatformUser
from app.core.mock_oauth import is_mock_mode


class TwitterAdapter(BaseAdapter):
    """Adapter for Twitter/X API v2."""
    
    BASE_URL = "https://api.twitter.com/2"
    
    def __init__(self, access_token: str):
        """
        Initialize Twitter adapter.
        
        Args:
            access_token: Twitter OAuth 2.0 access token
        """
        super().__init__(access_token, "twitter")
    
    async def publish_post(
        self,
        content: str,
        media_url: Optional[str] = None,
        media_type: Optional[str] = None
    ) -> PostResult:
        """
        Publish a tweet to Twitter/X.
        
        Twitter has a 280 character limit.
        Images and videos require separate media upload then tweet.
        """
        
        # Check character limit (280 chars for regular tweets)
        if len(content) > 280:
            return PostResult(
                success=False,
                platform=self.platform,
                error_message=f"Tweet exceeds 280 character limit (current: {len(content)})"
            )
        
        # Mock mode for testing
        if is_mock_mode():
            return PostResult(
                success=True,
                platform=self.platform,
                platform_post_id=f"mock_tw_post_{hash(content) % 10000}",
                posted_at=datetime.utcnow(),
                raw_response={
                    "data": {
                        "id": f"mock_tw_post_{hash(content) % 10000}",
                        "text": content[:100]
                    }
                }
            )
        
        # Real API call
        try:
            async with httpx.AsyncClient() as client:
                headers = {
                    "Authorization": f"Bearer {self.access_token}",
                    "Content-Type": "application/json"
                }
                
                # Prepare tweet data
                tweet_data = {"text": content}
                
                # TODO: Add media support when needed
                # Twitter requires media upload first, then attach to tweet
                
                response = await client.post(
                    f"{self.BASE_URL}/tweets",
                    headers=headers,
                    json=tweet_data
                )
                response.raise_for_status()
                result = response.json()
                
                return PostResult(
                    success=True,
                    platform=self.platform,
                    platform_post_id=result.get("data", {}).get("id"),
                    posted_at=datetime.utcnow(),
                    raw_response=result
                )
                
        except httpx.HTTPStatusError as e:
            error_detail = e.response.json() if e.response else str(e)
            return PostResult(
                success=False,
                platform=self.platform,
                error_message=f"Twitter API error: {error_detail}"
            )
        except Exception as e:
            return PostResult(
                success=False,
                platform=self.platform,
                error_message=f"Unexpected error: {str(e)}"
            )
    
    async def post_thread(self, tweets: list[str]) -> list[PostResult]:
        """
        Post a thread of multiple tweets.
        
        Args:
            tweets: List of tweet texts (max 25 tweets per thread)
        
        Returns:
            List of PostResult for each tweet
        """
        results = []
        
        for i, tweet_content in enumerate(tweets):
            result = await self.publish_post(tweet_content)
            results.append(result)
            
            # Small delay between tweets (rate limiting)
            import asyncio
            await asyncio.sleep(1)
        
        return results
    
    async def reply_to_tweet(
        self,
        tweet_id: str,
        content: str
    ) -> PostResult:
        """
        Reply to an existing tweet.
        
        Args:
            tweet_id: ID of the tweet to reply to
            content: Reply content
        """
        
        if is_mock_mode():
            return PostResult(
                success=True,
                platform=self.platform,
                platform_post_id=f"mock_tw_reply_{hash(content) % 10000}",
                posted_at=datetime.utcnow(),
                raw_response={"reply_to": tweet_id}
            )
        
        try:
            async with httpx.AsyncClient() as client:
                headers = {
                    "Authorization": f"Bearer {self.access_token}",
                    "Content-Type": "application/json"
                }
                
                reply_data = {
                    "text": content,
                    "reply": {"in_reply_to_tweet_id": tweet_id}
                }
                
                response = await client.post(
                    f"{self.BASE_URL}/tweets",
                    headers=headers,
                    json=reply_data
                )
                response.raise_for_status()
                result = response.json()
                
                return PostResult(
                    success=True,
                    platform=self.platform,
                    platform_post_id=result.get("data", {}).get("id"),
                    posted_at=datetime.utcnow(),
                    raw_response=result
                )
                
        except Exception as e:
            return PostResult(
                success=False,
                platform=self.platform,
                error_message=f"Failed to reply: {str(e)}"
            )
    
    async def get_user_info(self) -> PlatformUser:
        """Get Twitter user information."""
        
        if is_mock_mode():
            return PlatformUser(
                platform_user_id="mock_twitter_11111",
                name="Mock Twitter User",
                username="mock_twitter_user",
                email="mock_twitter@example.com"
            )
        
        try:
            async with httpx.AsyncClient() as client:
                headers = {"Authorization": f"Bearer {self.access_token}"}
                
                response = await client.get(
                    f"{self.BASE_URL}/users/me",
                    headers=headers,
                    params={"user.fields": "id,name,username,email"}
                )
                response.raise_for_status()
                data = response.json().get("data", {})
                
                return PlatformUser(
                    platform_user_id=data.get("id"),
                    name=data.get("name"),
                    username=data.get("username"),
                    email=data.get("email")
                )
        except Exception as e:
            print(f"Error getting Twitter user: {e}")
            return PlatformUser(
                platform_user_id="unknown",
                name="Unknown User"
            )
    
    async def check_rate_limit(self) -> Dict:
        """Check Twitter API rate limits."""
        
        if is_mock_mode():
            return {
                "remaining": 45,
                "limit": 50,
                "reset_time": datetime.utcnow().timestamp() + 900  # 15 minutes
            }
        
        # Twitter rate limits are in response headers
        return {"remaining": "check headers", "limit": 50}