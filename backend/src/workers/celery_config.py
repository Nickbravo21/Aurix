# Celery worker configuration
from .core.config import settings

# Broker & Backend
broker_url = str(settings.celery_broker_url)
result_backend = str(settings.celery_result_backend)

# Task settings
task_serializer = "json"
accept_content = ["json"]
result_serializer = "json"
timezone = "UTC"
enable_utc = True

# Performance
worker_prefetch_multiplier = 4
worker_max_tasks_per_child = 1000

# Task routes
task_routes = {
    "aurix.workers.tasks.ingest.*": {"queue": "ingestion"},
    "aurix.workers.tasks.refresh_kpis.*": {"queue": "analytics"},
    "aurix.workers.tasks.forecast.*": {"queue": "analytics"},
    "aurix.workers.tasks.send_reports.*": {"queue": "reports"},
}

# Task time limits
task_soft_time_limit = 300  # 5 minutes
task_time_limit = 600  # 10 minutes

# Result expiration
result_expires = 3600  # 1 hour
