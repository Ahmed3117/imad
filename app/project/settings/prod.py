"""
Production settings.
Activated when DJANGO_ENV=prod in the environment / .env file.
"""
from .base import *

# ─────────────────────────────────────────────
# Security
# ─────────────────────────────────────────────
DEBUG = False

ALLOWED_HOSTS = [
    'nabbiuwny.com',
    'www.nabbiuwny.com',
    '50.19.183.215',
    'localhost',
]

CSRF_TRUSTED_ORIGINS = [
    'https://nabbiuwny.com',
    'https://www.nabbiuwny.com',
]

SECURE_CROSS_ORIGIN_OPENER_POLICY = 'same-origin'

# ─────────────────────────────────────────────
# Static files – collectstatic writes here;
# Nginx serves from this directory.
# ─────────────────────────────────────────────
STATIC_ROOT = os.path.join(BASE_DIR, 'staticfiles')

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
