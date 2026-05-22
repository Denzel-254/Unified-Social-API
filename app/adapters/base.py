"""Base adapter interface for all social media platforms."""

from abc import ABC, abstractmethod
from typing import Dict, Any, Optional
from dataclasses import dataclass
from datetime import datetime


@dataclass
class PostResult:
    """Result of publishing to a platform."""
    success: bool
    platform: str
    platform_post_id: Optional[str] = None
    error_message: Optional[str] = None
    posted_at: Optional[datetime] = None
    raw_response: Optional[Dict] = None


@dataclass
class PlatformUser:
    """Platform user information."""
    platform_user_id: str
    name: str
    email: Optional[str] = None
    username: Optional[str] = None
    profile_url: Optional[str] = None


class BaseAdapter(ABC):
    """Abstract base class for all platform adapters."""
    
    def __init__(self, access_token: str, platform: str):
        """
        Initialize adapter with access token.
        
        Args:
            access_token: OAuth access token for the platform
            platform: Name of the platform (facebook, instagram, etc.)
        """
        self.access_token = access_token
        self.platform = platform
    
    @abstractmethod
    async def publish_post(
        self,
        content: str,
        media_url: Optional[str] = None,
        media_type: Optional[str] = None
    ) -> PostResult:
        """
        Publish content to the platform.
        
        Args:
            content: Text content to publish
            media_url: Optional URL to image/video
            media_type: Type of media ('image', 'video', or None)
            
        Returns:
            PostResult with details of the published post
        """
        pass
    
    @abstractmethod
    async def get_user_info(self) -> PlatformUser:
        """
        Get platform user information.
        
        Returns:
            PlatformUser with user details
        """
        pass
    
    @abstractmethod
    async def check_rate_limit(self) -> Dict:
        """
        Check current rate limit status.
        
        Returns:
            Dictionary with rate limit information
        """
        pass
    
    async def refresh_token_if_needed(self) -> bool:
        """
        Refresh the access token if expired.
        Returns True if token was refreshed.
        """
        # Will be implemented by child classes if needed
        return False