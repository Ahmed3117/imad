"""
Production settings.
Activated when DJANGO_ENV=prod in the environment / .env file.
"""
from .base import *

# ─────────────────────────────────────────────
# Security
# ─────────────────────────────────────────────
DEBUG = True

ALLOWED_HOSTS = [
    'nabbiuwny.com',
    'www.nabbiuwny.com',
    '50.19.183.215',
    '127.0.0.1',
    'localhost',
    '127.0.0.1:7777',
    'localhost:7777',
]

CSRF_TRUSTED_ORIGINS = [
    'https://nabbiuwny.com',
    'https://www.nabbiuwny.com',
    'http://127.0.0.1:7777',
    'http://localhost:7777',
]

SECURE_CROSS_ORIGIN_OPENER_POLICY = 'same-origin'

# ─────────────────────────────────────────────
# Static files – collectstatic writes here;
# Nginx serves from this directory.
# ─────────────────────────────────────────────
STATIC_ROOT = os.path.join(BASE_DIR, 'static')

# ─────────────────────────────────────────────
# Channels – Redis channel layer for production
# Set REDIS_URL in your environment, e.g.:
#   REDIS_URL=redis://redis:6379/0
# ─────────────────────────────────────────────
CHANNEL_LAYERS = {
    "default": {
        "BACKEND": "channels_redis.core.RedisChannelLayer",
        "CONFIG": {
            "hosts": [os.environ.get("REDIS_URL", "redis://redis:6379/0")],
        },
    }
}

REDIS_URL = os.environ.get("REDIS_URL", "redis://redis:6379/0")

# If DEBUG is True, serve static files locally via runserver
if DEBUG:
    STATICFILES_DIRS = [
        os.path.join(BASE_DIR, 'static'),
    ]
    STATIC_ROOT = os.path.join(BASE_DIR, 'staticfiles_collected_dummy')
