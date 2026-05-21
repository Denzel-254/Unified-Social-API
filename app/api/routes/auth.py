"""Authentication routes - Simple version for testing."""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

router = APIRouter(prefix="/auth", tags=["authentication"])


class TokenResponse(BaseModel):
    """Token response model."""
    access_token: str
    token_type: str


@router.get("/{platform}/connect")
async def oauth_connect(platform: str):
    """Redirect to platform OAuth page."""
    return {
        "message": f"OAuth for {platform} will be implemented in Day 2",
        "platform": platform,
        "redirect_url": f"https://{platform}.com/oauth/authorize"
    }


@router.get("/{platform}/callback")
async def oauth_callback(platform: str, code: str = None):
    """Handle OAuth callback."""
    return {
        "message": f"OAuth callback for {platform} received",
        "code_received": code is not None
    }