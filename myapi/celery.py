# myapi/celery.py
import os
from celery import Celery

# Set the default Django settings module for the 'celery' program.
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'myapi.settings')

# Create an instance of the Celery application.
app = Celery('myapi')

# Load task modules from all registered Django apps.
app.config_from_object('django.conf:settings', namespace='CELERY')

# Auto-discover tasks in all installed apps.
app.autodiscover_tasks()