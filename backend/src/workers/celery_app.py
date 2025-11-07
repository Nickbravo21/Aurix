"""
Celery application for background tasks.
"""
from celery import Celery

from ..core.config import settings

# Create Celery app
celery_app = Celery(
    "aurix",
    broker=str(settings.celery_broker_url),
    backend=str(settings.celery_result_backend),
)

# Load config
celery_app.config_from_object("src.workers.celery_config")

# Auto-discover tasks
celery_app.autodiscover_tasks(["src.workers.tasks"])
