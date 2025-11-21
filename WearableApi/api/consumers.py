"""
WebSocket consumers para notificaciones en tiempo real.
"""

import json
import logging
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async
from .models import Notificacion

logger = logging.getLogger(__name__)


class NotificationConsumer(AsyncWebsocketConsumer):
    """
    Consumer para manejar notificaciones en tiempo real para un consumidor específico.
    
    URL: ws://localhost:8000/ws/notificaciones/{consumidor_id}/
    """
    
    async def connect(self):
        """Manejar nueva conexión WebSocket"""
        self.consumidor_id = self.scope['url_route']['kwargs']['consumidor_id']
        self.room_group_name = f'notifications_{self.consumidor_id}'

        logger.info(f"🔌 WebSocket connecting for consumidor {self.consumidor_id}")

        # Unirse al grupo de notificaciones del consumidor
        await self.channel_layer.group_add(
            self.room_group_name,
            self.channel_name
        )

        # Aceptar la conexión
        await self.accept()
        
        logger.info(f"✅ WebSocket connected for consumidor {self.consumidor_id}")
        
        # Enviar notificaciones existentes al conectar
        try:
            notificaciones = await self.get_unread_notifications()
            await self.send(text_data=json.dumps({
                'type': 'initial_notifications',
                'notifications': notificaciones
            }))
            logger.info(f"📬 Sent {len(notificaciones)} initial notifications")
        except Exception as e:
            logger.error(f"Error sending initial notifications: {e}")

    async def disconnect(self, close_code):
        """Manejar desconexión WebSocket"""
        logger.info(f"🔌 WebSocket disconnecting for consumidor {self.consumidor_id} (code: {close_code})")
        
        # Salir del grupo de notificaciones
        await self.channel_layer.group_discard(
            self.room_group_name,
            self.channel_name
        )

    async def receive(self, text_data):
        """
        Recibir mensaje desde el cliente WebSocket.
        
        Mensajes soportados:
        - {"type": "mark_read", "notification_id": 123}
        - {"type": "ping"}
        """
        try:
            data = json.loads(text_data)
            msg_type = data.get('type')
            
            if msg_type == 'mark_read':
                notification_id = data.get('notification_id')
                if notification_id:
                    await self.mark_notification_read(notification_id)
                    
                    # Confirmar al cliente
                    await self.send(text_data=json.dumps({
                        'type': 'marked_read',
                        'notification_id': notification_id
                    }))
                    logger.info(f"✓ Notification {notification_id} marked as read")
            
            elif msg_type == 'ping':
                # Responder a ping para mantener conexión activa
                await self.send(text_data=json.dumps({
                    'type': 'pong'
                }))
                
            else:
                logger.warning(f"Unknown message type: {msg_type}")
                
        except json.JSONDecodeError as e:
            logger.error(f"Invalid JSON received: {e}")
        except Exception as e:
            logger.error(f"Error handling received message: {e}")

    async def notification_message(self, event):
        """
        Recibir mensaje desde el channel layer (enviado por signals).
        Reenviar la notificación al cliente WebSocket.
        """
        try:
            await self.send(text_data=json.dumps({
                'type': 'new_notification',
                'notification': event['notification']
            }))
            logger.info(f"🆕 Sent new notification to consumidor {self.consumidor_id}")
        except Exception as e:
            logger.error(f"Error sending notification message: {e}")

    @database_sync_to_async
    def get_unread_notifications(self):
        """Obtener notificaciones no leídas del consumidor"""
        try:
            notificaciones = Notificacion.objects.filter(
                consumidor_id=self.consumidor_id,
                leida=False
            ).order_by('-fecha_envio')[:20]
            
            return [{
                'id': n.id,
                'tipo': n.tipo,
                'contenido': n.contenido,
                'fecha_envio': n.fecha_envio.isoformat(),
                'leida': n.leida,
                'deseo_id': n.deseo_id if hasattr(n, 'deseo_id') else None,
            } for n in notificaciones]
        except Exception as e:
            logger.error(f"Error fetching unread notifications: {e}")
            return []

    @database_sync_to_async
    def mark_notification_read(self, notification_id):
        """Marcar notificación como leída"""
        try:
            notificacion = Notificacion.objects.get(
                id=notification_id,
                consumidor_id=self.consumidor_id
            )
            notificacion.mark_read()
            logger.debug(f"Marked notification {notification_id} as read")
        except Notificacion.DoesNotExist:
            logger.warning(f"Notification {notification_id} not found")
        except Exception as e:
            logger.error(f"Error marking notification as read: {e}")