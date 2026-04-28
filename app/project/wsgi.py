"""
WSGI config for project project.

It exposes the WSGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/4.0/howto/deployment/wsgi/
"""

import os

# Load .env so DJANGO_ENV is available before Django boots
try:
    import dotenv
    from pathlib import Path
    dotenv.load_dotenv(Path(__file__).resolve().parent.parent / '.env')
except ImportError:
    pass

from django.core.wsgi import get_wsgi_application

django_env = os.environ.get('DJANGO_ENV', 'local')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', f'project.settings.{django_env}')

application = get_wsgi_application()
