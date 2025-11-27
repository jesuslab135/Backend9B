"""
WebSocket consumers para datos en tiempo real.
"""

import json
import logging
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async
from django.db.models import Avg, Max, Min, StdDev
from .models import Notificacion, Lectura, Ventana, Deseo, Analisis

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


class SensorDataConsumer(AsyncWebsocketConsumer):
    """
    Consumer para datos de sensores en tiempo real (ESP32).
    
    URL: ws://localhost:8000/ws/sensor-data/{consumidor_id}/
    """
    
    async def connect(self):
        self.consumidor_id = self.scope['url_route']['kwargs']['consumidor_id']
        self.room_group_name = f'sensor_data_{self.consumidor_id}'

        logger.info(f"🔌 SensorData WebSocket connecting for consumidor {self.consumidor_id}")

        await self.channel_layer.group_add(
            self.room_group_name,
            self.channel_name
        )

        await self.accept()
        logger.info(f"✅ SensorData WebSocket connected for consumidor {self.consumidor_id}")
        
        # Enviar últimas 10 lecturas al conectar
        try:
            lecturas = await self.get_recent_lecturas()
            await self.send(text_data=json.dumps({
                'type': 'initial_data',
                'lecturas': lecturas
            }))
            logger.info(f"📊 Sent {len(lecturas)} initial sensor readings")
        except Exception as e:
            logger.error(f"Error sending initial sensor data: {e}")

    async def disconnect(self, close_code):
        logger.info(f"🔌 SensorData WebSocket disconnecting for consumidor {self.consumidor_id}")
        await self.channel_layer.group_discard(
            self.room_group_name,
            self.channel_name
        )

    async def receive(self, text_data):
        """Handle ping/pong to keep connection alive"""
        try:
            data = json.loads(text_data)
            if data.get('type') == 'ping':
                await self.send(text_data=json.dumps({'type': 'pong'}))
        except Exception as e:
            logger.error(f"Error in SensorData receive: {e}")

    async def sensor_update(self, event):
        """Recibir actualización de sensor desde channel layer"""
        try:
            await self.send(text_data=json.dumps({
                'type': 'sensor_update',
                'lectura': event['lectura']
            }))
            logger.debug(f"📡 Sent sensor update to consumidor {self.consumidor_id}")
        except Exception as e:
            logger.error(f"Error sending sensor update: {e}")

    @database_sync_to_async
    def get_recent_lecturas(self):
        """Obtener últimas 10 lecturas del consumidor"""
        try:
            from .models import Consumidor
            consumidor = Consumidor.objects.get(id=self.consumidor_id)
            
            lecturas = Lectura.objects.filter(
                ventana__consumidor=consumidor
            ).select_related('ventana').order_by('-created_at')[:10]
            
            return [{
                'id': l.id,
                'heart_rate': float(l.heart_rate) if l.heart_rate else None,
                'accel_x': float(l.accel_x) if l.accel_x else None,
                'accel_y': float(l.accel_y) if l.accel_y else None,
                'accel_z': float(l.accel_z) if l.accel_z else None,
                'gyro_x': float(l.gyro_x) if l.gyro_x else None,
                'gyro_y': float(l.gyro_y) if l.gyro_y else None,
                'gyro_z': float(l.gyro_z) if l.gyro_z else None,
                'created_at': l.created_at.isoformat(),
            } for l in lecturas]
        except Exception as e:
            logger.error(f"Error fetching recent lecturas: {e}")
            return []


class HeartRateConsumer(AsyncWebsocketConsumer):
    """
    Consumer para datos de frecuencia cardíaca agregados.
    
    URL: ws://localhost:8000/ws/heart-rate/{consumidor_id}/
    """
    
    async def connect(self):
        self.consumidor_id = self.scope['url_route']['kwargs']['consumidor_id']
        self.room_group_name = f'heart_rate_{self.consumidor_id}'

        logger.info(f"🔌 HeartRate WebSocket connecting for consumidor {self.consumidor_id}")

        await self.channel_layer.group_add(
            self.room_group_name,
            self.channel_name
        )

        await self.accept()
        logger.info(f"✅ HeartRate WebSocket connected for consumidor {self.consumidor_id}")
        
        # Enviar datos iniciales
        try:
            hr_data = await self.get_heart_rate_data()
            await self.send(text_data=json.dumps({
                'type': 'initial_data',
                'data': hr_data
            }))
            logger.info(f"💓 Sent initial heart rate data")
        except Exception as e:
            logger.error(f"Error sending initial HR data: {e}")

    async def disconnect(self, close_code):
        logger.info(f"🔌 HeartRate WebSocket disconnecting for consumidor {self.consumidor_id}")
        await self.channel_layer.group_discard(
            self.room_group_name,
            self.channel_name
        )

    async def receive(self, text_data):
        try:
            data = json.loads(text_data)
            if data.get('type') == 'ping':
                await self.send(text_data=json.dumps({'type': 'pong'}))
        except Exception as e:
            logger.error(f"Error in HeartRate receive: {e}")

    async def hr_update(self, event):
        """Recibir actualización de HR desde channel layer"""
        try:
            await self.send(text_data=json.dumps({
                'type': 'hr_update',
                'data': event['data']
            }))
            logger.debug(f"💓 Sent HR update to consumidor {self.consumidor_id}")
        except Exception as e:
            logger.error(f"Error sending HR update: {e}")

    @database_sync_to_async
    def get_heart_rate_data(self):
        """Obtener estadísticas y ventanas de HR"""
        try:
            from datetime import datetime
            from django.utils import timezone
            from .models import Consumidor
            
            consumidor = Consumidor.objects.get(id=self.consumidor_id)
            
            # Ventanas del día actual
            today_start = timezone.now().replace(hour=0, minute=0, second=0, microsecond=0)
            
            ventanas = Ventana.objects.filter(
                consumidor=consumidor,
                window_start__gte=today_start
            ).order_by('-window_start')
            
            ventanas_data = [{
                'id': v.id,
                'window_start': v.window_start.isoformat(),
                'window_end': v.window_end.isoformat(),
                'heart_rate_mean': float(v.hr_mean) if v.hr_mean else None,
                'heart_rate_std': float(v.hr_std) if v.hr_std else None,
            } for v in ventanas]
            
            # Estadísticas generales
            ventanas_with_data = ventanas.exclude(hr_mean__isnull=True)
            stats = ventanas_with_data.aggregate(
                promedio=Avg('hr_mean'),
                minimo=Min('hr_mean'),
                maximo=Max('hr_mean'),
                desviacion=Avg('hr_std')
            )
            
            # Promedio del día
            promedio_dia = stats['promedio']
            
            return {
                'ventanas': ventanas_data,
                'promedio_dia': float(promedio_dia) if promedio_dia else None,
                'total_ventanas': len(ventanas_data),
                'ventanas_con_datos': ventanas_with_data.count(),
                'stats': {
                    'promedio': float(stats['promedio']) if stats['promedio'] else None,
                    'minimo': float(stats['minimo']) if stats['minimo'] else None,
                    'maximo': float(stats['maximo']) if stats['maximo'] else None,
                    'desviacion': float(stats['desviacion']) if stats['desviacion'] else None,
                }
            }
        except Exception as e:
            logger.error(f"Error fetching heart rate data: {e}")
            return {
                'ventanas': [],
                'promedio_dia': None,
                'total_ventanas': 0,
                'ventanas_con_datos': 0,
                'stats': {}
            }


class DesiresConsumer(AsyncWebsocketConsumer):
    """
    Consumer para datos de deseos/cravings.
    
    URL: ws://localhost:8000/ws/desires/{consumidor_id}/
    """
    
    async def connect(self):
        try:
            self.consumidor_id = self.scope['url_route']['kwargs']['consumidor_id']
            self.room_group_name = f'desires_{self.consumidor_id}'

            logger.info(f"🔌 Desires WebSocket connecting for consumidor {self.consumidor_id}")

            await self.channel_layer.group_add(
                self.room_group_name,
                self.channel_name
            )

            await self.accept()
            logger.info(f"✅ Desires WebSocket connected for consumidor {self.consumidor_id}")
            
            # Enviar datos iniciales
            try:
                desires_data = await self.get_desires_data()
                logger.info(f"📊 Desires data fetched: {len(desires_data.get('stats', []))} stats, {len(desires_data.get('tracking', []))} tracking")
                
                await self.send(text_data=json.dumps({
                    'type': 'initial_data',
                    'data': desires_data
                }))
                logger.info(f"🚬 Sent initial desires data")
            except Exception as e:
                logger.error(f"Error sending initial desires data: {e}")
                import traceback
                logger.error(traceback.format_exc())
                # Don't close connection, just send empty data
                await self.send(text_data=json.dumps({
                    'type': 'initial_data',
                    'data': {'stats': [], 'tracking': []}
                }))
        except Exception as e:
            logger.error(f"Error in Desires WebSocket connect: {e}")
            import traceback
            logger.error(traceback.format_exc())
            await self.close()

    async def disconnect(self, close_code):
        logger.info(f"🔌 Desires WebSocket disconnecting for consumidor {self.consumidor_id}")
        await self.channel_layer.group_discard(
            self.room_group_name,
            self.channel_name
        )

    async def receive(self, text_data):
        try:
            data = json.loads(text_data)
            if data.get('type') == 'ping':
                await self.send(text_data=json.dumps({'type': 'pong'}))
        except Exception as e:
            logger.error(f"Error in Desires receive: {e}")

    async def desire_update(self, event):
        """Recibir actualización de deseos desde channel layer"""
        try:
            await self.send(text_data=json.dumps({
                'type': 'desire_update',
                'data': event['data']
            }))
            logger.debug(f"🚬 Sent desire update to consumidor {self.consumidor_id}")
        except Exception as e:
            logger.error(f"Error sending desire update: {e}")

    @database_sync_to_async
    def get_desires_data(self):
        """Obtener estadísticas y tracking de deseos"""
        try:
            from django.db.models import Count, Q, F, Case, When, FloatField
            from .models import Consumidor, DeseoTipoChoices
            
            consumidor = Consumidor.objects.get(id=self.consumidor_id)
            
            # Estadísticas por tipo de deseo
            stats = []
            
            # Iterar sobre los tipos de deseo definidos en DeseoTipoChoices
            for tipo_choice in DeseoTipoChoices.choices:
                tipo_value = tipo_choice[0]  # e.g., 'comida'
                tipo_label = tipo_choice[1]  # e.g., 'Comida'
                
                deseos = Deseo.objects.filter(
                    consumidor=consumidor,
                    tipo=tipo_value
                )
                total = deseos.count()
                resueltos = deseos.filter(resolved=True).count()
                porcentaje = (resueltos / total * 100) if total > 0 else 0
                
                # Solo incluir tipos que tienen al menos un deseo
                if total > 0:
                    stats.append({
                        'deseo_tipo': tipo_label,
                        'total_deseos': total,
                        'deseos_resueltos': resueltos,
                        'porcentaje_resolucion': round(porcentaje, 1)
                    })
            
            # Timeline de deseos (últimos 20)
            deseos = Deseo.objects.filter(
                consumidor=consumidor
            ).order_by('-created_at')[:20]
            
            tracking = []
            for deseo in deseos:
                # Obtener análisis relacionado para probabilidad
                analisis = None
                if deseo.ventana:
                    analisis = Analisis.objects.filter(
                        usuario=consumidor.usuario,
                        ventana=deseo.ventana
                    ).first()
                
                # Obtener HR durante el deseo
                hr_durante = None
                if deseo.ventana and deseo.ventana.hr_mean:
                    hr_durante = float(deseo.ventana.hr_mean)
                
                # Get human-readable tipo
                tipo_label = dict(DeseoTipoChoices.choices).get(deseo.tipo, deseo.tipo)
                
                tracking.append({
                    'deseo_id': deseo.id,
                    'fecha_creacion': deseo.created_at.isoformat(),
                    'deseo_tipo': tipo_label,
                    'resolved': deseo.resolved,
                    'heart_rate_durante': hr_durante,
                    'probabilidad_modelo': float(analisis.probabilidad) if analisis and analisis.probabilidad else None
                })
            
            return {
                'stats': stats,
                'tracking': tracking
            }
        except Exception as e:
            logger.error(f"Error fetching desires data: {e}")
            import traceback
            logger.error(traceback.format_exc())
            return {
                'stats': [],
                'tracking': []
            }