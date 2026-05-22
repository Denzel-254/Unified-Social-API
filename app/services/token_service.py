"""Token management service for storing and refreshing OAuth tokens."""

from datetime import datetime, timedelta
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.models.token import PlatformToken
from app.models.user import User

class TokenService:
    """Handle OAuth token storage and refresh."""
    
    @staticmethod
    async def save_token(
        db: AsyncSession,
        user_id: int,
        platform: str,
        access_token: str,
        refresh_token: str = None,
        expires_in: int = None,
        platform_user_id: str = None
    ) -> PlatformToken:
        """Save or update OAuth token for a user."""
        
        # Check if token already exists
        query = select(PlatformToken).where(
            PlatformToken.user_id == user_id,
            PlatformToken.platform == platform
        )
        result = await db.execute(query)
        token_record = result.scalar_one_or_none()
        
        # Calculate expiration datetime
        expires_at = None
        if expires_in:
            expires_at = datetime.utcnow() + timedelta(seconds=expires_in)
        
        if token_record:
            # Update existing token
            token_record.access_token = access_token
            if refresh_token:
                token_record.refresh_token = refresh_token
            if expires_at:
                token_record.expires_at = expires_at
            if platform_user_id:
                token_record.platform_user_id = platform_user_id
            token_record.updated_at = datetime.utcnow()
        else:
            # Create new token
            token_record = PlatformToken(
                user_id=user_id,
                platform=platform,
                access_token=access_token,
                refresh_token=refresh_token,
                expires_at=expires_at,
                platform_user_id=platform_user_id
            )
            db.add(token_record)
        
        await db.commit()
        await db.refresh(token_record)
        return token_record
    
    @staticmethod
    async def get_token(
        db: AsyncSession,
        user_id: int,
        platform: str
    ) -> PlatformToken:
        """Retrieve a user's token for a platform."""
        
        query = select(PlatformToken).where(
            PlatformToken.user_id == user_id,
            PlatformToken.platform == platform
        )
        result = await db.execute(query)
        return result.scalar_one_or_none()
    
    @staticmethod
    async def is_token_expired(token: PlatformToken) -> bool:
        """Check if a token has expired."""
        if not token.expires_at:
            return False
        return token.expires_at <= datetime.utcnow()
    
    @staticmethod
    async def refresh_token_if_needed(
        db: AsyncSession,
        user_id: int,
        platform: str
    ) -> PlatformToken:
        """Refresh token if it's expired."""
        
        token = await TokenService.get_token(db, user_id, platform)
        
        if not token:
            return None
        
        if await TokenService.is_token_expired(token) and token.refresh_token:
            # TODO: Implement actual refresh logic for each platform
            # This will be added when we implement platform adapters
            pass
        
        return token