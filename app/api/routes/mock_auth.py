"""Mock OAuth endpoints for testing without real credentials."""

from fastapi import APIRouter, Request, HTTPException, Depends
from fastapi.responses import HTMLResponse, RedirectResponse
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.database import get_db
from app.core.mock_oauth import (
    get_mock_user_info,
    get_mock_token_response,
    MOCK_USERS
)
from app.services.token_service import TokenService

router = APIRouter(prefix="/mock", tags=["mock-oauth"])

# Temporary user ID for testing
CURRENT_USER_ID = 1


@router.get("/login", response_class=HTMLResponse)
async def mock_login_page(
    platform: str,
    state: str,
    redirect_uri: str
):
    """Mock OAuth consent screen - looks like real platform login."""
    
    # Get mock user data safely
    mock_user = MOCK_USERS.get(platform, {})
    user_name = mock_user.get('name', 'Test User')
    user_email = mock_user.get('email', 'test@example.com')
    
    html_content = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <title>Mock OAuth - {platform.title()} Login</title>
        <style>
            body {{
                font-family: Arial, sans-serif;
                display: flex;
                justify-content: center;
                align-items: center;
                height: 100vh;
                margin: 0;
                background: #f5f5f5;
            }}
            .container {{
                background: white;
                padding: 40px;
                border-radius: 10px;
                box-shadow: 0 2px 10px rgba(0,0,0,0.1);
                text-align: center;
                max-width: 400px;
            }}
            h1 {{ color: #333; }}
            .platform {{
                font-size: 24px;
                color: #1877f2;
                margin: 20px 0;
            }}
            button {{
                background: #1877f2;
                color: white;
                border: none;
                padding: 12px 30px;
                border-radius: 5px;
                font-size: 16px;
                cursor: pointer;
                margin: 10px;
            }}
            button:hover {{
                background: #166fe5;
            }}
            .cancel {{
                background: #ccc;
                color: #333;
            }}
            .cancel:hover {{
                background: #bbb;
            }}
            .info {{
                color: #666;
                font-size: 12px;
                margin-top: 20px;
                border-top: 1px solid #eee;
                padding-top: 20px;
            }}
        </style>
    </head>
    <body>
        <div class="container">
            <h1>Mock {platform.title()} OAuth</h1>
            <div class="platform"> {platform.title()} Platform</div>
            <p><strong>Mock User:</strong> {user_name}</p>
            <p><strong>Email:</strong> {user_email}</p>
            <form method="get" action="{redirect_uri}">
                <input type="hidden" name="code" value="mock_auth_code_{platform}">
                <input type="hidden" name="state" value="{state}">
                <button type="submit">Authorize {platform.title()}</button>
            </form>
            <form method="get" action="/">
                <button type="submit" class="cancel"> Cancel</button>
            </form>
            <div class="info">
                Mock Mode - No real credentials required<br>
                This simulates the OAuth consent screen for testing
            </div>
        </div>
    </body>
    </html>
    """
    return HTMLResponse(content=html_content)


@router.get("/token")
async def mock_token_endpoint(
    code: str,
    platform: str = None
):
    """Mock token exchange endpoint."""
    
    # Extract platform from code
    if not platform:
        if "_" in code:
            platform = code.split("_")[-1]
        else:
            platform = "facebook"
    
    # Get mock token response
    token_response = get_mock_token_response(platform, code)
    
    if "error" in token_response:
        raise HTTPException(status_code=400, detail=token_response["error"])
    
    return token_response


@router.post("/token")
async def mock_token_endpoint_post(
    code: str,
    grant_type: str = "authorization_code"
):
    """Mock token exchange endpoint (POST version)."""
    
    return await mock_token_endpoint(code)


@router.get("/userinfo")
async def mock_userinfo(
    access_token: str,
    platform: str = None
):
    """Get mock user info."""
    
    # Try to find platform from token
    for plat, user in MOCK_USERS.items():
        if user["access_token"] == access_token:
            platform = plat
            break
    
    if not platform:
        raise HTTPException(status_code=401, detail="Invalid token")
    
    user_info = get_mock_user_info(platform, access_token)
    
    if "error" in user_info:
        raise HTTPException(status_code=401, detail=user_info["error"])
    
    return user_info