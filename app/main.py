"""FastAPI application entry point."""

from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.core.config import settings
from app.core.database import engine, Base
from app.api.routes import auth  # Import routes

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Handle startup and shutdown events."""
    # Startup: Create database tables
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    print(f"Database tables created. Using: {settings.database_url}")
    print(f"API Docs available at: http://localhost:8000/docs")
    yield
    # Shutdown: Clean up resources
    await engine.dispose()
    print("Database connection closed")

# Create FastAPI app
app = FastAPI(
    title=settings.app_name,
    description="Unified API for publishing content across multiple social media platforms",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan,
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(auth.router)

@app.get("/")
async def root():
    """Health check endpoint."""
    return {
        "message": f"Welcome to {settings.app_name}",
        "status": "operational",
        "version": "1.0.0",
        "database_type": "SQLite (development)",
        "endpoints": ["/docs", "/health", "/auth/{platform}/connect", "/auth/{platform}/callback"]
    }

@app.get("/health")
async def health_check():
    """Detailed health check."""
    return {
        "status": "healthy",
        "database": "connected",
        "api_version": "1.0.0",
        "debug_mode": settings.debug
    }