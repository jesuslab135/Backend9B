"""
Django signals para enviar notificaciones automáticamente por WebSocket.
"""

import logging
from django.db.models.signals import post_save
from django.dispatch import receiver
from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync
from .models import Notificacion

logger = logging.getLogger(__name__)


@receiver(post_save, sender=Notificacion)
def notificacion_created(sender, instance, created, **kwargs):
    """
    Cuando se crea una notificación, enviarla automáticamente por WebSocket
    al consumidor correspondiente.
    
    Args:
        sender: Model class (Notificacion)
        instance: Instancia de Notificacion creada
        created: True si es nueva, False si es update
        **kwargs: Argumentos adicionales del signal
    """
    # Solo enviar si es una nueva notificación no leída
    if created and not instance.leida:
        try:
            channel_layer = get_channel_layer()
            
            # Nombre del grupo del consumidor
            room_group_name = f'notifications_{instance.consumidor_id}'
            
            # Datos de la notificación
            notification_data = {
                'id': instance.id,
                'tipo': instance.tipo,
                'contenido': instance.contenido,
                'fecha_envio': instance.fecha_envio.isoformat(),
                'leida': instance.leida,
                'deseo_id': instance.deseo_id if hasattr(instance, 'deseo_id') else None,
            }
            
            # Enviar a todos los WebSockets del grupo
            async_to_sync(channel_layer.group_send)(
                room_group_name,
                {
                    'type': 'notification_message',  # Llama al método del consumer
                    'notification': notification_data
                }
            )
            
            logger.info(
                f"[WebSocket] Notification {instance.id} sent to group '{room_group_name}'"
            )
            
        except Exception as e:
            logger.error(f"[WebSocket] Error sending notification: {e}")
            # No lanzar excepción para no interrumpir el guardado