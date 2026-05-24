"""Celery worker entry point."""

from app.core.celery_app import celery_app
from app.tasks import publish_tasks, analytics_tasks  # Import to register tasks

if __name__ == "__main__":
    celery_app.start()