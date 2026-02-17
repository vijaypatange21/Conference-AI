"""
conference_ai/celery.py

Celery configuration for async task processing.

Setup:
- Uses Redis as broker (localhost:6379 by default)
- Auto-discovers tasks from all apps
- Configured for Django ORM usage

In production:
- Use Redis cluster or RabbitMQ for HA
- Configure worker pools, timeouts, retries
- Use monitoring tools: Flower, Sentry
"""

import os
from celery import Celery

# Set default Django settings module
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'conference_ai.settings')

app = Celery('conference_ai')

# Load config from Django settings
app.config_from_object('django.conf:settings', namespace='CELERY')

# Auto-discover tasks from all apps
app.autodiscover_tasks()


@app.task(bind=True)
def debug_task(self):
    """Test task - remove in production."""
    print(f'Request: {self.request!r}')
