"""OAuth 2.0 helper functions for social media platforms."""

from typing import Dict, Optional
from authlib.integrations.httpx_client import AsyncOAuth2Client
from app.core.config import settings
from app.core.mock_oauth import is_mock_mode, get_mock_authorize_url, get_mock_token_response

# OAuth configuration for each platform
OAUTH_CONFIG = {
    "facebook": {
        "client_id": settings.meta_app_id,
        "client_secret": settings.meta_app_secret,
        "authorize_url": "https://www.facebook.com/v18.0/dialog/oauth",
        "access_token_url": "https://graph.facebook.com/v18.0/oauth/access_token",
        "scope": ["pages_manage_posts", "pages_read_engagement", "public_profile"],
        "redirect_uri": "/api/v1/auth/facebook/callback"
    },
    "instagram": {
        "client_id": settings.meta_app_id,
        "client_secret": settings.meta_app_secret,
        "authorize_url": "https://api.instagram.com/oauth/authorize",
        "access_token_url": "https://api.instagram.com/oauth/access_token",
        "scope": ["instagram_basic", "instagram_content_publish", "pages_read_engagement"],
        "redirect_uri": "/api/v1/auth/instagram/callback"
    },
    "twitter": {
        "client_id": settings.twitter_api_key,
        "client_secret": settings.twitter_api_secret,
        "authorize_url": "https://twitter.com/i/oauth2/authorize",
        "access_token_url": "https://api.twitter.com/2/oauth2/token",
        "scope": ["tweet.read", "tweet.write", "users.read", "offline.access"],
        "redirect_uri": "/api/v1/auth/twitter/callback"
    },
    "linkedin": {
        "client_id": settings.linkedin_client_id,
        "client_secret": settings.linkedin_client_secret,
        "authorize_url": "https://www.linkedin.com/oauth/v2/authorization",
        "access_token_url": "https://www.linkedin.com/oauth/v2/accessToken",
        "scope": ["r_liteprofile", "r_emailaddress", "w_member_social"],
        "redirect_uri": "/api/v1/auth/linkedin/callback"
    },
    "youtube": {
        "client_id": settings.youtube_client_id,
        "client_secret": settings.youtube_client_secret,
        "authorize_url": "https://accounts.google.com/o/oauth2/v2/auth",
        "access_token_url": "https://oauth2.googleapis.com/token",
        "scope": ["https://www.googleapis.com/auth/youtube.upload"],
        "redirect_uri": "/api/v1/auth/youtube/callback"
    },
    "whatsapp": {
        "client_id": settings.meta_app_id,
        "client_secret": settings.meta_app_secret,
        "authorize_url": "https://www.facebook.com/v18.0/dialog/oauth",
        "access_token_url": "https://graph.facebook.com/v18.0/oauth/access_token",
        "scope": ["whatsapp_business_messaging"],
        "redirect_uri": "/api/v1/auth/whatsapp/callback"
    }
}


def get_oauth_client(platform: str, redirect_uri: str = None) -> Optional[AsyncOAuth2Client]:
    """Create an OAuth2 client for the specified platform."""
    
    config = OAUTH_CONFIG.get(platform)
    if not config:
        return None
    
    # In mock mode, return a dummy client
    if is_mock_mode():
        return MockOAuthClient(platform)
    
    if not config["client_id"] or not config["client_secret"]:
        return None
    
    # Build full redirect URI
    if redirect_uri and not redirect_uri.startswith("http"):
        redirect_uri = f"http://localhost:8000{redirect_uri}"
    
    return AsyncOAuth2Client(
        client_id=config["client_id"],
        client_secret=config["client_secret"],
        redirect_uri=redirect_uri or config["redirect_uri"],
        scope=config["scope"],
    )


class MockOAuthClient:
    """Mock OAuth client for testing without real credentials."""
    
    def __init__(self, platform: str):
        self.platform = platform
        self.redirect_uri = None
    
    def create_authorization_url(self, url, state):
        """Create a mock authorization URL."""
        from app.core.mock_oauth import get_mock_authorize_url
        
        # Use mock authorize URL
        mock_url = get_mock_authorize_url(
            platform=self.platform,
            state=state,
            redirect_uri=self.redirect_uri or "http://localhost:8000/mock/callback"
        )
        return mock_url, state
    
    async def fetch_token(self, url, code, redirect_uri, grant_type):
        """Fetch a mock token."""
        from app.core.mock_oauth import get_mock_token_response
        
        self.redirect_uri = redirect_uri
        return get_mock_token_response(self.platform, code)