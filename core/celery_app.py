from celery import Celery

from core.config import settings

celery_app = Celery(
    "worker",
    broker=settings.CELERY_BROKER_URL,
    backend=settings.CELERY_RESULT_BACKEND,
    include=[
        "core.tasks",
    ],
)

# Celery configuration
celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="Africa/Nairobi",
    enable_utc=True,
    task_routes={
        "core.tasks.*": {"queue": "main"},
        "core.tasks.send_sms_notification": {"queue": "notifications"},
        "core.tasks.process_mpesa_payment": {"queue": "payments"},
    },
    task_annotations={
        "core.tasks.send_sms_notification": {"rate_limit": "10/m"},
        "core.tasks.process_mpesa_payment": {"rate_limit": "30/m"},
    },
)

# Import tasks to ensure they are registered
from core import tasks  # noqa
