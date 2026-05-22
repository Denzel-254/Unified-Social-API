"""Mock OAuth for testing without real credentials."""

from typing import Dict, Optional
import uuid
from datetime import datetime, timedelta

# Mock data for testing
MOCK_USERS = {
    "facebook": {
        "id": "mock_facebook_12345",
        "name": "Mock Facebook User",
        "email": "mock_facebook@example.com",
        "access_token": "mock_fb_token_" + str(uuid.uuid4()),
        "refresh_token": "mock_fb_refresh_" + str(uuid.uuid4()),
        "expires_in": 7200  # 2 hours
    },
    "instagram": {
        "id": "mock_instagram_67890",
        "name": "Mock Instagram User",
        "email": "mock_instagram@example.com",
        "access_token": "mock_ig_token_" + str(uuid.uuid4()),
        "refresh_token": "mock_ig_refresh_" + str(uuid.uuid4()),
        "expires_in": 7200
    },
    "twitter": {
        "id": "mock_twitter_11111",
        "name": "Mock Twitter User",
        "email": "mock_twitter@example.com",
        "access_token": "mock_tw_token_" + str(uuid.uuid4()),
        "refresh_token": "mock_tw_refresh_" + str(uuid.uuid4()),
        "expires_in": 7200
    },
    "linkedin": {
        "id": "mock_linkedin_22222",
        "name": "Mock LinkedIn User",
        "email": "mock_linkedin@example.com",
        "access_token": "mock_li_token_" + str(uuid.uuid4()),
        "refresh_token": "mock_li_refresh_" + str(uuid.uuid4()),
        "expires_in": 7200
    },
    "youtube": {
        "id": "mock_youtube_33333",
        "name": "Mock YouTube User",
        "email": "mock_youtube@example.com",
        "access_token": "mock_yt_token_" + str(uuid.uuid4()),
        "refresh_token": "mock_yt_refresh_" + str(uuid.uuid4()),
        "expires_in": 7200
    },
    "whatsapp": {
        "id": "mock_whatsapp_44444",
        "name": "Mock WhatsApp Business",
        "email": "mock_whatsapp@example.com",
        "access_token": "mock_wa_token_" + str(uuid.uuid4()),
        "refresh_token": "mock_wa_refresh_" + str(uuid.uuid4()),
        "expires_in": 7200
    }
}

# Mock OAuth URLs (for simulation)
MOCK_AUTHORIZE_URL = "http://localhost:8000/mock/authorize"
MOCK_TOKEN_URL = "http://localhost:8000/mock/token"


def is_mock_mode() -> bool:
    """Check if mock mode is enabled."""
    import os
    return os.getenv("MOCK_OAUTH", "true").lower() == "true"  # Default to true for testing


def get_mock_authorize_url(platform: str, state: str, redirect_uri: str) -> str:
    """Generate a mock authorize URL that simulates the OAuth consent screen."""
    return f"http://localhost:8000/mock/login?platform={platform}&state={state}&redirect_uri={redirect_uri}"


def get_mock_token_response(platform: str, code: str) -> Dict:
    """Generate a mock token response."""
    user = MOCK_USERS.get(platform)
    if not user:
        return {"error": "Invalid platform"}
    
    return {
        "access_token": user["access_token"],
        "refresh_token": user["refresh_token"],
        "expires_in": user["expires_in"],
        "token_type": "bearer",
        "scope": "read write",
        "platform_user_id": user["id"]
    }


def get_mock_user_info(platform: str, access_token: str) -> Dict:
    """Get mock user info for a platform."""
    user = MOCK_USERS.get(platform)
    if not user or user["access_token"] != access_token:
        return {"error": "Invalid token"}
    
    return {
        "id": user["id"],
        "name": user["name"],
        "email": user["email"],
        "platform": platform
    }