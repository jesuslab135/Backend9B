# 🔌 WebSockets & Django Channels - Configuración y Diagnóstico

## 📋 Estado Actual

### ✅ Configuración Correcta

1. **ASGI Configuration** (`WearableApi/asgi.py`)
   - ✅ ProtocolTypeRouter configurado
   - ✅ AuthMiddlewareStack implementado
   - ✅ AllowedHostsOriginValidator agregado
   - ✅ WebSocket routing importado correctamente

2. **Consumer** (`api/consumers.py`)
   - ✅ NotificationConsumer implementado
   - ✅ Métodos async correctos: connect, disconnect, receive
   - ✅ Manejo de notificaciones en tiempo real
   - ✅ Sistema de ping/pong para mantener conexión
   - ✅ Marcado de notificaciones como leídas

3. **Routing** (`api/routing.py`)
   - ✅ WebSocket URL pattern definido: `ws/notificaciones/{consumidor_id}/`

4. **Signals** (`api/signals.py`)
   - ✅ Signal post_save configurado para Notificacion
   - ✅ Envío automático por WebSocket cuando se crea notificación
   - ✅ Registrado en `api/apps.py` ready()

5. **Settings** (`WearableApi/settings.py`)
   - ✅ 'daphne' en INSTALLED_APPS (primera posición)
   - ✅ 'channels' en INSTALLED_APPS
   - ✅ ASGI_APPLICATION configurado (**AGREGADO**)
   - ✅ CHANNEL_LAYERS con Redis configurado

---

## ❌ Problema Identificado

### **Django Channels NO está instalado**

Los errores reportados indican que las librerías no están disponibles:
```
Import "channels.routing" could not be resolved from source
Import "channels.generic.websocket" could not be resolved from source
Import "channels.layers" could not be resolved from source
```

---

## 🔧 Solución

### Paso 1: Instalar Django Channels y Dependencias

```bash
# Navegar al directorio del proyecto
cd "c:\Users\MSI\Desktop\9B\Proyecto 9B\API_wearable\Simulador-0910\WearableApi"

# Instalar las dependencias necesarias
pip install channels==4.0.0 channels-redis==4.1.0 daphne==4.0.0
```

**Paquetes que se instalarán:**
- `channels==4.0.0` - Django Channels para WebSockets
- `channels-redis==4.1.0` - Backend Redis para channel layers
- `daphne==4.0.0` - Servidor ASGI para ejecutar WebSockets

---

### Paso 2: Verificar Instalación

```bash
# Verificar que Channels se instaló correctamente
py -c "import channels; print(f'✅ Django Channels {channels.__version__} instalado')"

# Verificar que channels-redis se instaló
py -c "import channels_redis; print('✅ channels-redis instalado')"

# Verificar que daphne se instaló
py -c "import daphne; print('✅ Daphne instalado')"
```

---

### Paso 3: Verificar que Redis está corriendo

```bash
# Verificar conexión a Redis
py -c "import redis; r = redis.Redis(host='localhost', port=6379, db=0); r.ping(); print('✅ Redis conectado')"
```

Si Redis no está corriendo:
```bash
# Iniciar Redis (si está instalado)
redis-server

# O usar Docker
docker run -d -p 6379:6379 redis:latest
```

---

### Paso 4: Ejecutar con Daphne (servidor ASGI)

Para soportar WebSockets, debes usar Daphne en lugar de `runserver`:

```bash
# Ejecutar con Daphne
daphne -b 0.0.0.0 -p 8000 WearableApi.asgi:application

# O con logging detallado
daphne -b 0.0.0.0 -p 8000 -v 2 WearableApi.asgi:application
```

**Nota:** `py manage.py runserver` NO soporta WebSockets. Debes usar Daphne.

---

## 🧪 Probar WebSockets

### Opción 1: Desde JavaScript (Frontend)

```javascript
// Conectar al WebSocket
const ws = new WebSocket('ws://localhost:8000/ws/notificaciones/1/');

// Cuando se conecta
ws.onopen = () => {
    console.log('✅ WebSocket conectado');
};

// Recibir mensajes
ws.onmessage = (event) => {
    const data = JSON.parse(event.data);
    console.log('📬 Notificación recibida:', data);
};

// Enviar ping
ws.send(JSON.stringify({ type: 'ping' }));

// Marcar notificación como leída
ws.send(JSON.stringify({
    type: 'mark_read',
    notification_id: 123
}));
```

---

### Opción 2: Desde Python (Test Script)

Crear archivo `test_websocket.py`:

```python
import asyncio
import websockets
import json

async def test_websocket():
    uri = "ws://localhost:8000/ws/notificaciones/1/"
    
    async with websockets.connect(uri) as websocket:
        print("✅ Conectado al WebSocket")
        
        # Recibir notificaciones iniciales
        initial = await websocket.recv()
        print(f"📬 Notificaciones iniciales: {initial}")
        
        # Enviar ping
        await websocket.send(json.dumps({"type": "ping"}))
        
        # Recibir pong
        pong = await websocket.recv()
        print(f"🏓 Respuesta: {pong}")
        
        # Mantener conexión abierta
        while True:
            message = await websocket.recv()
            print(f"📨 Mensaje recibido: {message}")

# Ejecutar
asyncio.run(test_websocket())
```

Ejecutar:
```bash
pip install websockets
py test_websocket.py
```

---

### Opción 3: Herramienta Online

Usar **WebSocket King** o similar:
- URL: `ws://localhost:8000/ws/notificaciones/1/`
- Enviar: `{"type": "ping"}`
- Deberías recibir: `{"type": "pong"}`

---

## 📊 Estructura de Mensajes WebSocket

### Cliente → Servidor

**1. Ping (mantener conexión)**
```json
{
  "type": "ping"
}
```

**2. Marcar notificación como leída**
```json
{
  "type": "mark_read",
  "notification_id": 123
}
```

---

### Servidor → Cliente

**1. Notificaciones iniciales (al conectar)**
```json
{
  "type": "initial_notifications",
  "notifications": [
    {
      "id": 1,
      "tipo": "recordatorio",
      "contenido": "¡Recuerda registrar tu formulario!",
      "fecha_envio": "2025-11-17T10:30:00",
      "leida": false,
      "deseo_id": null
    }
  ]
}
```

**2. Nueva notificación (tiempo real)**
```json
{
  "type": "new_notification",
  "notification": {
    "id": 2,
    "tipo": "alerta",
    "contenido": "Alta probabilidad de craving detectada",
    "fecha_envio": "2025-11-17T11:00:00",
    "leida": false,
    "deseo_id": 5
  }
}
```

**3. Confirmación de lectura**
```json
{
  "type": "marked_read",
  "notification_id": 123
}
```

**4. Pong (respuesta a ping)**
```json
{
  "type": "pong"
}
```

---

## 🔍 Debugging

### Ver logs de WebSocket

```python
# En consumers.py ya está configurado logging
import logging
logger = logging.getLogger(__name__)
```

Los logs aparecerán en:
- `logs/debug.log` - Todos los mensajes
- `logs/info.log` - Conexiones y mensajes importantes
- `logs/error.log` - Errores

---

### Verificar Channel Layer

```python
# Test en Django shell
py manage.py shell

from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync

channel_layer = get_channel_layer()

# Enviar mensaje de prueba
async_to_sync(channel_layer.group_send)(
    'notifications_1',
    {
        'type': 'notification_message',
        'notification': {
            'id': 999,
            'tipo': 'test',
            'contenido': 'Test desde shell'
        }
    }
)
```

---

## 📦 Dependencias en requirements.txt

Ya están definidas correctamente:
```txt
channels==4.0.0
channels-redis==4.1.0
daphne==4.0.0
```

---

## 🚀 Comandos Rápidos

```bash
# 1. Instalar dependencias
pip install -r requirements.txt

# 2. Verificar instalación
py -c "import channels, channels_redis, daphne; print('✅ Todo instalado')"

# 3. Iniciar Redis (si no está corriendo)
redis-server

# 4. Ejecutar servidor con WebSockets
daphne -b 0.0.0.0 -p 8000 WearableApi.asgi:application
```

---

## ✅ Checklist Final

- [ ] Django Channels instalado (`pip install channels==4.0.0`)
- [ ] channels-redis instalado (`pip install channels-redis==4.1.0`)
- [ ] Daphne instalado (`pip install daphne==4.0.0`)
- [ ] Redis corriendo en localhost:6379
- [ ] ASGI_APPLICATION configurado en settings.py ✅
- [ ] Servidor corriendo con Daphne (NO con runserver)
- [ ] WebSocket probado desde cliente

---

## 🐛 Problemas Comunes

### 1. "No module named 'channels'"
**Solución:** `pip install channels==4.0.0`

### 2. "Connection refused" al conectar WebSocket
**Solución:** Asegúrate de usar Daphne, no runserver

### 3. "Can't connect to Redis"
**Solución:** Iniciar Redis: `redis-server`

### 4. WebSocket se desconecta inmediatamente
**Solución:** Verificar CORS y ALLOWED_HOSTS en settings.py

### 5. Signal no envía notificaciones
**Solución:** Verificar que `api.signals` está importado en `api/apps.py`

---

## 📚 Recursos

- [Django Channels Docs](https://channels.readthedocs.io/)
- [WebSocket Protocol](https://datatracker.ietf.org/doc/html/rfc6455)
- [Daphne Server](https://github.com/django/daphne)

---

## 🎯 Próximos Pasos

1. Instalar las dependencias
2. Ejecutar con Daphne
3. Probar conexión WebSocket
4. Integrar con frontend
5. Agregar autenticación JWT a WebSockets (opcional)
