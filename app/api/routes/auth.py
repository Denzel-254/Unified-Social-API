"""Authentication routes - Complete OAuth implementation."""

from fastapi import APIRouter, HTTPException, Request, Depends
from fastapi.responses import RedirectResponse
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.database import get_db
from app.core.oauth import get_oauth_client, OAUTH_CONFIG
from app.services.token_service import TokenService
from app.core.mock_oauth import is_mock_mode
from app.core.config import settings


router = APIRouter(prefix="/auth", tags=["authentication"])

# Temporary user storage (replace with real auth in Day 3)
CURRENT_USER_ID = 1


# ============================================================
# SPECIFIC YOUTUBE ROUTES (MUST BE FIRST - BEFORE GENERIC ROUTES)
# ============================================================

@router.get("/youtube-test")
async def youtube_test():
    """Simple test to check if route works."""
    return {"message": "YouTube test route works!"}


@router.get("/youtube/connect")
async def youtube_connect(request: Request):
    """YouTube OAuth connection - Real implementation."""
    
    print("=" * 50)
    print("YouTube OAuth Started")
    
    if is_mock_mode():
        print("   Using MOCK mode")
        state = "mock_state_123"
        redirect_uri = str(request.url_for("oauth_callback", platform="youtube"))
        from app.core.mock_oauth import get_mock_authorize_url
        mock_url = get_mock_authorize_url("youtube", state, redirect_uri)
        return RedirectResponse(url=mock_url)
    
    print("Using REAL Google OAuth")
    print(f"Client ID: {settings.youtube_client_id[:20]}...")
    
    from authlib.integrations.httpx_client import AsyncOAuth2Client
    
    redirect_uri = "http://localhost:8000/api/v1/auth/youtube/callback"
    
    client = AsyncOAuth2Client(
        client_id=settings.youtube_client_id,
        client_secret=settings.youtube_client_secret,
        redirect_uri=redirect_uri,
        scope=[
            "https://www.googleapis.com/auth/youtube.upload",
            "https://www.googleapis.com/auth/youtube.readonly",
            "openid",
            "email",
            "profile"
        ]
    )
    
    authorization_url, state = client.create_authorization_url(
        "https://accounts.google.com/o/oauth2/v2/auth",
        access_type="offline",
        prompt="consent"
    )
    
    print(f"Redirecting to Google...")
    print("=" * 50)
    
    return RedirectResponse(url=authorization_url)


@router.get("/youtube/callback")
async def youtube_callback(
    request: Request,
    code: str = None,
    error: str = None,
    state: str = None,
    db: AsyncSession = Depends(get_db)
):
    """YouTube OAuth callback."""
    
    print(">>> YouTube Callback Called")
    print(f">>> Code: {code[:20] if code else 'None'}")
    print(f">>> Error: {error}")
    
    if error:
        raise HTTPException(status_code=400, detail=f"OAuth error: {error}")
    
    if not code:
        raise HTTPException(status_code=400, detail="No authorization code received")
    
    try:
        from authlib.integrations.httpx_client import AsyncOAuth2Client
        import httpx
        
        redirect_uri = "http://localhost:8000/api/v1/auth/youtube/callback"
        
        client = AsyncOAuth2Client(
            client_id=settings.youtube_client_id,
            client_secret=settings.youtube_client_secret,
            redirect_uri=redirect_uri
        )
        
        token_response = await client.fetch_token(
            "https://oauth2.googleapis.com/token",
            code=code,
            grant_type="authorization_code"
        )
        
        access_token = token_response.get("access_token")
        refresh_token = token_response.get("refresh_token")
        expires_in = token_response.get("expires_in")
        
        # Get user info
        async with httpx.AsyncClient() as http_client:
            user_info = await http_client.get(
                "https://www.googleapis.com/oauth2/v2/userinfo",
                headers={"Authorization": f"Bearer {access_token}"}
            )
            user_data = user_info.json()
            platform_user_id = user_data.get("id")
        
        token = await TokenService.save_token(
            db=db,
            user_id=CURRENT_USER_ID,
            platform="youtube",
            access_token=access_token,
            refresh_token=refresh_token,
            expires_in=expires_in,
            platform_user_id=platform_user_id
        )
        
        return {
            "message": "Successfully connected to YouTube",
            "platform": "youtube",
            "platform_user_id": platform_user_id,
            "token_expires_at": token.expires_at.isoformat() if token.expires_at else None
        }
        
    except Exception as e:
        print(f">>> Error: {e}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================
# GENERIC ROUTES (FOR MOCK MODE AND OTHER PLATFORMS)
# ============================================================

@router.get("/{platform}/connect")
async def oauth_connect(
    platform: str,
    request: Request
):
    """Step 1: Redirect user to platform's OAuth consent screen."""
    
    # Check if we're in mock mode
    if is_mock_mode():
        state = "mock_state_123"
        redirect_uri = str(request.url_for("oauth_callback", platform=platform))
        from app.core.mock_oauth import get_mock_authorize_url
        mock_url = get_mock_authorize_url(platform, state, redirect_uri)
        return RedirectResponse(url=mock_url)
    
    # For platforms with dedicated routes, they would have been caught above
    raise HTTPException(status_code=501, detail=f"Real OAuth for {platform} not implemented yet. Please use the platform-specific endpoint if available.")


@router.get("/{platform}/callback")
async def oauth_callback(
    platform: str,
    request: Request,
    code: str = None,
    state: str = None,
    error: str = None,
    db: AsyncSession = Depends(get_db)
):
    """Handle OAuth callback and exchange code for access token."""
    
    if error:
        raise HTTPException(status_code=400, detail=f"OAuth error: {error}")
    
    if not code:
        raise HTTPException(status_code=400, detail="No authorization code received")
    
    # Check if mock mode
    if is_mock_mode():
        from app.core.mock_oauth import get_mock_token_response
        token_response = get_mock_token_response(platform, code)
        access_token = token_response.get("access_token")
        refresh_token = token_response.get("refresh_token")
        expires_in = token_response.get("expires_in")
        platform_user_id = token_response.get("platform_user_id")
    else:
        # Use real OAuth token exchange
        client = get_oauth_client(platform)
        config = OAUTH_CONFIG[platform]
        redirect_uri = str(request.url_for("oauth_callback", platform=platform))
        
        token_response = await client.fetch_token(
            config["access_token_url"],
            code=code,
            redirect_uri=redirect_uri,
            grant_type="authorization_code"
        )
        
        access_token = token_response.get("access_token")
        refresh_token = token_response.get("refresh_token")
        expires_in = token_response.get("expires_in")
        
        # Get platform user ID from real API
        platform_user_id = await get_platform_user_id(platform, access_token)
    
    # Save token to database (same for both mock and real)
    token = await TokenService.save_token(
        db=db,
        user_id=CURRENT_USER_ID,
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


# ============================================================
# HELPER FUNCTIONS
# ============================================================

async def get_platform_user_id(platform: str, access_token: str) -> str:
    """Get the user's platform-specific ID."""
    
    import httpx
    
    try:
        async with httpx.AsyncClient() as client:
            if platform == "facebook":
                response = await client.get(
                    "https://graph.facebook.com/v18.0/me",
                    params={"access_token": access_token}
                )
                data = response.json()
                return data.get("id")
            
            elif platform == "instagram":
                response = await client.get(
                    "https://graph.facebook.com/v18.0/me/accounts",
                    params={"access_token": access_token}
                )
                data = response.json()
                if data.get("data"):
                    return data["data"][0].get("id")
                return "unknown"
            
            elif platform == "twitter":
                response = await client.get(
                    "https://api.twitter.com/2/users/me",
                    headers={"Authorization": f"Bearer {access_token}"}
                )
                data = response.json()
                return data.get("data", {}).get("id")
            
            elif platform == "linkedin":
                response = await client.get(
                    "https://api.linkedin.com/v2/userinfo",
                    headers={"Authorization": f"Bearer {access_token}"}
                )
                data = response.json()
                return data.get("sub")
            
            elif platform == "youtube":
                response = await client.get(
                    "https://www.googleapis.com/oauth2/v2/userinfo",
                    headers={"Authorization": f"Bearer {access_token}"}
                )
                data = response.json()
                return data.get("id")
            
            return "unknown"
            
    except Exception as e:
        print(f"Error getting platform user ID: {e}")
        return "unknown"