import os

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")

from channels.auth import AuthMiddlewareStack
from channels.routing import ProtocolTypeRouter, URLRouter
from channels.security.websocket import OriginValidator
from django.conf import settings
from django.core.asgi import get_asgi_application

http_application = get_asgi_application()
from config.routing import websocket_urlpatterns

application = ProtocolTypeRouter({
    "http": http_application,
    "websocket": OriginValidator(
        AuthMiddlewareStack(URLRouter(websocket_urlpatterns)),
        settings.CSRF_TRUSTED_ORIGINS,
    ),
})
