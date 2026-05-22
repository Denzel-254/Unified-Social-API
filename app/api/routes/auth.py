"""Authentication routes - Complete OAuth implementation."""

from fastapi import APIRouter, HTTPException, Request, Depends
from fastapi.responses import RedirectResponse
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.database import get_db
from app.core.oauth import get_oauth_client, OAUTH_CONFIG
from app.services.token_service import TokenService
from app.core.mock_oauth import is_mock_mode


router = APIRouter(prefix="/auth", tags=["authentication"])

# Temporary user storage (replace with real auth in Day 3)
# For now, we'll use a hardcoded user ID 1
CURRENT_USER_ID = 1

@router.get("/{platform}/connect")
async def oauth_connect(
    platform: str,
    request: Request
):
    """
    Step 1: Redirect user to platform's OAuth consent screen.
    """
    
    # Check if we're in mock mode
    if is_mock_mode():
        # Generate a simple state
        state = "mock_state_123"
        
        # Build redirect URI
        redirect_uri = str(request.url_for("oauth_callback", platform=platform))
        
        # Use mock authorize URL
        from app.core.mock_oauth import get_mock_authorize_url
        mock_url = get_mock_authorize_url(platform, state, redirect_uri)
        
        return RedirectResponse(url=mock_url)
    



@router.get("/{platform}/callback")
async def oauth_callback(
    platform: str,
    request: Request,
    code: str = None,
    state: str = None,
    error: str = None,
    db: AsyncSession = Depends(get_db)
):
    """
    Step 2: Handle OAuth callback and exchange code for access token.
    """
    
    # Handle OAuth errors
    if error:
        raise HTTPException(status_code=400, detail=f"OAuth error: {error}")
    
    if not code:
        raise HTTPException(status_code=400, detail="No authorization code received")
    
    # Validate platform
    if platform not in OAUTH_CONFIG:
        raise HTTPException(status_code=400, detail=f"Platform '{platform}' not supported")
    
    try:
        # Create OAuth client
        client = get_oauth_client(platform)
        
        # Exchange code for access token
        config = OAUTH_CONFIG[platform]
        redirect_uri = str(request.url_for("oauth_callback", platform=platform))
        
        token_response = await client.fetch_token(
            config["access_token_url"],
            code=code,
            redirect_uri=redirect_uri,
            grant_type="authorization_code"
        )
        
        # Extract token information
        access_token = token_response.get("access_token")
        refresh_token = token_response.get("refresh_token")
        expires_in = token_response.get("expires_in")
        
        # Get platform user ID (different for each platform)
        platform_user_id = await get_platform_user_id(platform, access_token)
        
        # Save token to database
        token = await TokenService.save_token(
            db=db,
            user_id=CURRENT_USER_ID,  # TODO: Get actual user ID from auth
            platform=platform,
            access_token=access_token,
            refresh_token=refresh_token,
            expires_in=expires_in,
            platform_user_id=platform_user_id
        )
        
        return {
            "message": f"Successfully connected to {platform}",
            "platform": platform,
            "platform_user_id": platform_user_id,
            "token_expires_at": token.expires_at.isoformat() if token.expires_at else None
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Token exchange failed: {str(e)}")


@router.get("/{platform}/tokens")
async def get_user_tokens(
    platform: str,
    db: AsyncSession = Depends(get_db)
):
    """Get token information for a platform (for testing)."""
    
    token = await TokenService.get_token(db, CURRENT_USER_ID, platform)
    
    if not token:
        return {
            "platform": platform,
            "connected": False,
            "message": "No token found for this platform"
        }
    
    return {
        "platform": platform,
        "connected": True,
        "platform_user_id": token.platform_user_id,
        "expires_at": token.expires_at.isoformat() if token.expires_at else None,
        "is_expired": await TokenService.is_token_expired(token)
    }


async def get_platform_user_id(platform: str, access_token: str) -> str:
    """Get the user's platform-specific ID."""
    
    import httpx
    
    try:
        async with httpx.AsyncClient() as client:
            if platform == "facebook":
                # Get Facebook user ID
                response = await client.get(
                    "https://graph.facebook.com/v18.0/me",
                    params={"access_token": access_token}
                )
                data = response.json()
                return data.get("id")
            
            elif platform == "instagram":
                # Get Instagram user ID (requires Facebook page ID first)
                response = await client.get(
                    "https://graph.facebook.com/v18.0/me/accounts",
                    params={"access_token": access_token}
                )
                data = response.json()
                if data.get("data"):
                    return data["data"][0].get("id")
                return "unknown"
            
            elif platform == "twitter":
                # Get Twitter user ID
                response = await client.get(
                    "https://api.twitter.com/2/users/me",
                    headers={"Authorization": f"Bearer {access_token}"}
                )
                data = response.json()
                return data.get("data", {}).get("id")
            
            elif platform == "linkedin":
                # Get LinkedIn user ID
                response = await client.get(
                    "https://api.linkedin.com/v2/userinfo",
                    headers={"Authorization": f"Bearer {access_token}"}
                )
                data = response.json()
                return data.get("sub")
            
            return "unknown"
            
    except Exception as e:
        print(f"Error getting platform user ID: {e}")
        return "unknown"