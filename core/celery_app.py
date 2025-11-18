from celery import Celery
from celery.schedules import crontab

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
    beat_schedule={
        # Check due loans every day at 9 AM
        "check-due-loans-daily": {
            "task": "core.tasks.check_due_loans",
            "schedule": crontab(hour=9, minute=0),
        },
        # Check overdue loans every 6 hours
        "check-overdue-loans-6h": {
            "task": "core.tasks.check_overdue_loans",
            "schedule": crontab(hour="*/6"),
        },
        # Daily credit score recalculation at 2 AM
        "recalculate-credit-scores": {
            "task": "core.tasks.calculate_credit_score_batch",
            "schedule": crontab(hour=2, minute=0),
        },
    },
)

# Import tasks to ensure they are registered
from core import tasks  # noqa
