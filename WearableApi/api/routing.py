"""
WebSocket URL routing for the API app.
"""

from django.urls import re_path
from . import consumers

websocket_urlpatterns = [
    # WebSocket para notificaciones por consumidor
    re_path(
        r'ws/notificaciones/(?P<consumidor_id>\w+)/$',
        consumers.NotificationConsumer.as_asgi()
    ),
]