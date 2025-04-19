from __future__ import absolute_import, unicode_literals
import os
from celery import Celery

# Set default Django settings
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')

# Create Celery app
app = Celery('core')

# Load settings from Django settings file
app.config_from_object('django.conf:settings', namespace='CELERY')

# Auto-discover tasks in all installed apps
app.autodiscover_tasks()

# Specify the schedule filename explicitly
app.conf.beat_schedule_filename = '/home/easytech/manasa-api/src/celerybeat-schedule'

