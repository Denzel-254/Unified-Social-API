"""FastAPI application entry point."""

from contextlib import asynccontextmanager
from fastapi import FastAPI, APIRouter
from fastapi.middleware.cors import CORSMiddleware
from app.core.config import settings
from app.core.database import engine, Base, AsyncSessionLocal
from app.api.routes import auth, mock_auth, publish  # ← MAKE SURE publish IS IMPORTED
from app.services.user_service import UserService
from app.core.celery_app import celery_app


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Handle startup and shutdown events."""
    # Startup: Create database tables
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    
    # Create test user
    async with AsyncSessionLocal() as db:
        await UserService.get_or_create_test_user(db)
        print("Test user created (email: test@example.com)")
    
    # Start Celery (in production, you'd run separate worker)
    print("Celery configured for async tasks")
    print("Run 'celery -A celery_worker worker --loglevel=info' in another terminal for background tasks")
    
    print(f"API Docs: http://localhost:8000/docs")
    print(f"OAuth endpoints: http://localhost:8000{settings.api_v1_prefix}/auth/{{platform}}/connect")
    print(f"Celery Flower: http://localhost:5555 (if running)")
    yield
    
    # Shutdown
    await engine.dispose()
    print("Clean shutdown complete")


# Create FastAPI app
app = FastAPI(
    title=settings.app_name,
    description="Unified API for publishing across social media platforms",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan,
)

# Add CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Create versioned API router
api_router = APIRouter(prefix=settings.api_v1_prefix)
api_router.include_router(auth.router)
api_router.include_router(publish.router)  

# Include routers
app.include_router(api_router)
app.include_router(mock_auth.router)

# Root endpoints (no version prefix)
@app.get("/")
async def root():
    """Root endpoint."""
    return {
        "message": f"Welcome to {settings.app_name}",
        "status": "operational",
        "version": "1.0.0",
        "docs": "/docs",
        "api_endpoints": f"{settings.api_v1_prefix}/auth/{{platform}}/connect"
    }

@app.get("/health")
async def health_check():
    """Health check."""
    return {
        "status": "healthy",
        "database": "connected",
        "debug": settings.debug
    }