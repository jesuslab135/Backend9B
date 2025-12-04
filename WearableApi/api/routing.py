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
    
    # WebSocket para datos de sensores en tiempo real
    re_path(
        r'ws/sensor-data/(?P<consumidor_id>\w+)/$',
        consumers.SensorDataConsumer.as_asgi()
    ),
    # Alias con guión bajo para compatibilidad con frontend
    re_path(
        r'ws/sensor_data/(?P<consumidor_id>\w+)/$',
        consumers.SensorDataConsumer.as_asgi()
    ),
    
    # WebSocket para frecuencia cardíaca agregada
    re_path(
        r'ws/heart-rate/(?P<consumidor_id>\w+)/$',
        consumers.HeartRateConsumer.as_asgi()
    ),
    # Alias para compatibilidad con frontend (guiones bajos)
    re_path(
        r'ws/heart_rate_today/(?P<consumidor_id>\w+)/$',
        consumers.HeartRateConsumer.as_asgi()
    ),
    re_path(
        r'ws/heart_rate_stats/(?P<consumidor_id>\w+)/$',
        consumers.HeartRateConsumer.as_asgi()
    ),
    # Alias para compatibilidad con frontend (guiones)
    re_path(
        r'ws/heart-rate-today/(?P<consumidor_id>\w+)/$',
        consumers.HeartRateConsumer.as_asgi()
    ),
    re_path(
        r'ws/heart-rate-stats/(?P<consumidor_id>\w+)/$',
        consumers.HeartRateConsumer.as_asgi()
    ),
    
    # WebSocket para deseos/cravings
    re_path(
        r'ws/desires/(?P<consumidor_id>\w+)/$',
        consumers.DesiresConsumer.as_asgi()
    ),
]
