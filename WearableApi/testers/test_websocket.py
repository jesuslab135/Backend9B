"""
Script de prueba para WebSockets - Django Channels
Conecta al WebSocket y prueba la funcionalidad de notificaciones
"""

import asyncio
import json
import sys

try:
    import websockets
except ImportError:
    print("❌ Librería 'websockets' no instalada")
    print("📦 Instalar con: pip install websockets")
    sys.exit(1)

# Configuración
WEBSOCKET_URL = "ws://localhost:8000/ws/notificaciones/1/"

async def test_websocket_connection():
    """
    Prueba completa de la conexión WebSocket
    """
    print("="*70)
    print("🧪 PRUEBA DE WEBSOCKET - NOTIFICACIONES")
    print("="*70)
    print(f"\n🔗 Conectando a: {WEBSOCKET_URL}")
    
    try:
        async with websockets.connect(WEBSOCKET_URL) as websocket:
            print("✅ Conexión WebSocket establecida\n")
            
            # 1. Recibir notificaciones iniciales
            print("1️⃣ Esperando notificaciones iniciales...")
            try:
                initial_message = await asyncio.wait_for(websocket.recv(), timeout=5.0)
                data = json.loads(initial_message)
                print(f"📬 Tipo de mensaje: {data.get('type')}")
                
                if data.get('type') == 'initial_notifications':
                    notifications = data.get('notifications', [])
                    print(f"   Total notificaciones: {len(notifications)}")
                    if notifications:
                        print("   Notificaciones:")
                        for notif in notifications[:3]:  # Mostrar máximo 3
                            print(f"   - ID: {notif['id']}, Tipo: {notif['tipo']}")
                            print(f"     Contenido: {notif['contenido'][:50]}...")
                    else:
                        print("   (No hay notificaciones pendientes)")
            except asyncio.TimeoutError:
                print("⚠️ No se recibieron notificaciones iniciales (timeout)")
            
            # 2. Enviar ping
            print("\n2️⃣ Enviando PING...")
            ping_message = json.dumps({"type": "ping"})
            await websocket.send(ping_message)
            print(f"   📤 Enviado: {ping_message}")
            
            # Esperar PONG
            try:
                pong_response = await asyncio.wait_for(websocket.recv(), timeout=3.0)
                pong_data = json.loads(pong_response)
                if pong_data.get('type') == 'pong':
                    print(f"   📥 Recibido PONG: ✅")
                else:
                    print(f"   📥 Respuesta inesperada: {pong_data}")
            except asyncio.TimeoutError:
                print("   ⚠️ No se recibió PONG (timeout)")
            
            # 3. Probar marcar notificación como leída (ejemplo)
            print("\n3️⃣ Probando marcar notificación como leída...")
            mark_read_message = json.dumps({
                "type": "mark_read",
                "notification_id": 999  # ID de prueba
            })
            await websocket.send(mark_read_message)
            print(f"   📤 Enviado: {mark_read_message}")
            
            # Esperar confirmación
            try:
                response = await asyncio.wait_for(websocket.recv(), timeout=3.0)
                response_data = json.loads(response)
                print(f"   📥 Respuesta: {response_data}")
            except asyncio.TimeoutError:
                print("   ⚠️ No se recibió confirmación (timeout)")
            
            # 4. Mantener conexión abierta y esperar notificaciones en tiempo real
            print("\n4️⃣ Esperando notificaciones en tiempo real...")
            print("   (Presiona Ctrl+C para salir)")
            print("   💡 Tip: Crea una notificación en Django admin para probar\n")
            
            try:
                while True:
                    # Esperar mensajes con timeout de 60 segundos
                    try:
                        message = await asyncio.wait_for(websocket.recv(), timeout=60.0)
                        data = json.loads(message)
                        
                        if data.get('type') == 'new_notification':
                            notification = data.get('notification', {})
                            print(f"🆕 NUEVA NOTIFICACIÓN RECIBIDA:")
                            print(f"   ID: {notification.get('id')}")
                            print(f"   Tipo: {notification.get('tipo')}")
                            print(f"   Contenido: {notification.get('contenido')}")
                            print(f"   Fecha: {notification.get('fecha_envio')}")
                            print()
                        else:
                            print(f"📨 Mensaje recibido: {data}")
                            
                    except asyncio.TimeoutError:
                        # Enviar ping cada 60 segundos para mantener conexión
                        await websocket.send(json.dumps({"type": "ping"}))
                        print("   🏓 Ping enviado (mantener conexión activa)")
                        
            except KeyboardInterrupt:
                print("\n⚠️ Conexión interrumpida por usuario")
                
    except websockets.exceptions.WebSocketException as e:
        print(f"❌ Error WebSocket: {e}")
        print("\n💡 Posibles causas:")
        print("   1. El servidor NO está corriendo con Daphne")
        print("      Solución: daphne -b 0.0.0.0 -p 8000 WearableApi.asgi:application")
        print("   2. El servidor está en una URL diferente")
        print("   3. Redis no está disponible")
        return False
    except ConnectionRefusedError:
        print("❌ Conexión rechazada")
        print("\n💡 Asegúrate de que el servidor esté corriendo:")
        print("   daphne -b 0.0.0.0 -p 8000 WearableApi.asgi:application")
        return False
    except Exception as e:
        print(f"❌ Error inesperado: {e}")
        return False
    
    print("\n✅ Prueba completada exitosamente")
    return True

def main():
    """Ejecutar prueba"""
    print("\n⚠️ IMPORTANTE: Asegúrate de que el servidor esté corriendo con Daphne:")
    print("   daphne -b 0.0.0.0 -p 8000 WearableApi.asgi:application\n")
    
    try:
        # Ejecutar prueba asíncrona
        result = asyncio.run(test_websocket_connection())
        
        if result:
            print("\n" + "="*70)
            print("✅ PRUEBA EXITOSA - WebSockets funcionando correctamente")
            print("="*70)
        else:
            print("\n" + "="*70)
            print("❌ PRUEBA FALLIDA - Revisar errores arriba")
            print("="*70)
            
    except KeyboardInterrupt:
        print("\n\n⚠️ Prueba interrumpida por usuario")
    except Exception as e:
        print(f"\n❌ Error fatal: {e}")

if __name__ == "__main__":
    main()
