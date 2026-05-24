"""Simple user service for testing (temporary)."""

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.models.user import User

class UserService:
    """Handle user operations."""
    
    @staticmethod
    async def get_or_create_test_user(db: AsyncSession) -> User:
        """Get or create a test user for development."""
        
        # Try to get existing user
        query = select(User).where(User.email == "test@example.com")
        result = await db.execute(query)
        user = result.scalar_one_or_none()
        
        if not user:
            # Create test user
            user = User(
                email="test@example.com",
                hashed_password="temporary_password_hash",
                full_name="Test User",
                is_active=True
            )
            db.add(user)
            await db.commit()
            await db.refresh(user)
        
        return user