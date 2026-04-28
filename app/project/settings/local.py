"""
Local development settings.
Activated when DJANGO_ENV=local (or when DJANGO_ENV is not set).
"""
from .base import *

# ─────────────────────────────────────────────
# Security
# ─────────────────────────────────────────────
DEBUG = True

ALLOWED_HOSTS = [
    '*',
    'localhost',
    '127.0.0.1',
    '50.19.183.215',
    # Add your ngrok URL here when needed, e.g.:
    # '2a1e-45-100-68-117.ngrok-free.app',
]

CSRF_TRUSTED_ORIGINS = [
    'http://localhost:8000',
    'http://127.0.0.1:8000',
    # Add your ngrok URL here when needed, e.g.:
    # 'https://2a1e-45-100-68-117.ngrok-free.app',
]

SECURE_CROSS_ORIGIN_OPENER_POLICY = None

# ─────────────────────────────────────────────
# Database – SQLite for local dev (no MySQL needed)
# ─────────────────────────────────────────────
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'db.sqlite3',
    }
}

# ─────────────────────────────────────────────
# Zoom / BASE_URL – point to local server
# ─────────────────────────────────────────────
BASE_URL = 'http://127.0.0.1:8000'

# ─────────────────────────────────────────────
# Static files (no collectstatic needed locally)
# ─────────────────────────────────────────────
# STATIC_ROOT is intentionally not set in local — runserver serves from STATICFILES_DIRS

# ─────────────────────────────────────────────
# Channels – in-memory layer for local dev
# (no Redis required)
# ─────────────────────────────────────────────
CHANNEL_LAYERS = {
    "default": {
        "BACKEND": "channels.layers.InMemoryChannelLayer",
    }
}
