"""
Celery configuration for Claims Management System

This module configures Celery for background task processing.
Tasks include:
- RADAR synchronization
- Excel report generation
- Email notifications
- Data cleanup and maintenance

Setup:
1. Install Redis: https://redis.io/download
2. Install Celery: pip install celery redis
3. Start Redis: redis-server
4. Start Celery worker: celery -A claims_system worker -l info
5. Start Celery beat (scheduler): celery -A claims_system beat -l info
"""
import os
from celery import Celery
from celery.schedules import crontab

# Set the default Django settings module
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'claims_system.settings')

# Create Celery application
app = Celery('claims_system')

# Load configuration from Django settings with 'CELERY_' prefix
app.config_from_object('django.conf:settings', namespace='CELERY')

# Auto-discover tasks in all installed apps
app.autodiscover_tasks()


# Celery Beat Schedule (Periodic Tasks)
app.conf.beat_schedule = {
    # Sync RADAR data every 15 minutes
    'sync-radar-data': {
        'task': 'claims.tasks.sync_radar_data',
        'schedule': crontab(minute='*/15'),
    },

    # Check for time-barred claims daily at 8 AM
    'check-timebarred-claims': {
        'task': 'claims.tasks.check_timebarred_claims',
        'schedule': crontab(hour=8, minute=0),
    },

    # Generate daily analytics report at 9 AM
    'generate-daily-analytics': {
        'task': 'claims.tasks.generate_daily_analytics',
        'schedule': crontab(hour=9, minute=0),
    },

    # Cleanup old logs weekly (Sunday at 2 AM)
    'cleanup-old-logs': {
        'task': 'claims.tasks.cleanup_old_logs',
        'schedule': crontab(hour=2, minute=0, day_of_week=0),
    },
}

# Celery configuration
app.conf.update(
    # Task settings
    task_serializer='json',
    accept_content=['json'],
    result_serializer='json',
    timezone='UTC',
    enable_utc=True,

    # Task time limits
    task_soft_time_limit=300,  # 5 minutes soft limit
    task_time_limit=600,  # 10 minutes hard limit

    # Task result backend
    result_backend='redis://localhost:6379/1',
    result_expires=3600,  # Results expire after 1 hour

    # Worker settings
    worker_prefetch_multiplier=4,
    worker_max_tasks_per_child=1000,

    # Task routing
    task_routes={
        'claims.tasks.sync_radar_data': {'queue': 'radar'},
        'claims.tasks.generate_excel_export': {'queue': 'reports'},
        'claims.tasks.send_email_notification': {'queue': 'notifications'},
    },
)


@app.task(bind=True, ignore_result=True)
def debug_task(self):
    """Debug task for testing Celery setup"""
    print(f'Request: {self.request!r}')
