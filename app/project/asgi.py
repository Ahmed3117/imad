import os
import django

# Load .env so DJANGO_ENV is available before Django boots
try:
    import dotenv
    from pathlib import Path
    dotenv.load_dotenv(Path(__file__).resolve().parent.parent / '.env')
except ImportError:
    pass

django_env = os.environ.get('DJANGO_ENV', 'local')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', f'project.settings.{django_env}')

# Initialize Django before importing other modules
django.setup()

from django.core.asgi import get_asgi_application
from channels.routing import ProtocolTypeRouter, URLRouter
from chat.routing import websocket_urlpatterns
from channels.auth import AuthMiddlewareStack

application = ProtocolTypeRouter({
    "http": get_asgi_application(),
    "websocket": AuthMiddlewareStack(
        URLRouter(websocket_urlpatterns)
    ),
})
