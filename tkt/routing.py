from django.urls import re_path
from channels.routing import ProtocolTypeRouter, URLRouter
from . import consumers
from .consumers import NotificationConsumer
websocket_urlpatterns = [
    re_path(r'ws/notifications/$', NotificationConsumer.as_asgi()),
]

application = ProtocolTypeRouter(
    {
        "websocket": URLRouter(
            websocket_urlpatterns
        ),
    }
)
