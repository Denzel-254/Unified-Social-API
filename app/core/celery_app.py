"""Celery application configuration - with fallback for development."""

import os
from celery import Celery

# Try to use real Redis, but fallback to memory transport if not available
REDIS_AVAILABLE = False

try:
    import redis
    r = redis.Redis(host='localhost', port=6379, socket_connect_timeout=1)
    r.ping()
    REDIS_AVAILABLE = True
    print("✅ Redis connection successful")
except:
    print("⚠️ Redis not available, using in-memory transport for Celery")
    print("   Install Redis or use Docker for full async capabilities")

# Configure broker URL
if REDIS_AVAILABLE:
    broker_url = os.getenv("CELERY_BROKER_URL", "redis://localhost:6379/0")
    result_backend = os.getenv("CELERY_RESULT_BACKEND", "redis://localhost:6379/1")
else:
    # Use memory transport for development (no Redis needed)
    broker_url = "memory://"
    result_backend = "rpc://"

# Create Celery instance
celery_app = Celery(
    "unified_social_api",
    broker=broker_url,
    backend=result_backend
)

# Configure Celery
celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    task_track_started=True,
    task_always_eager=not REDIS_AVAILABLE,  # Run tasks synchronously if no Redis
    task_eager_propagates=not REDIS_AVAILABLE,
)

# Auto-discover tasks
celery_app.autodiscover_tasks(["app.tasks"])

print(f"📊 Celery configured with broker: {broker_url}")