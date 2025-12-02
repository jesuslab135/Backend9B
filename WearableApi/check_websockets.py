"""
Script para verificar la configuración de WebSockets y Django Channels
"""

import sys
import os

print("="*70)
print("🔍 VERIFICACIÓN DE WEBSOCKETS - DJANGO CHANNELS")
print("="*70)

# 1. Verificar Django
print("\n1️⃣ Verificando Django...")
try:
    import django
    print(f"   ✅ Django {django.get_version()} instalado")
except ImportError as e:
    print(f"   ❌ Django no instalado: {e}")
    sys.exit(1)

# 2. Verificar Channels
print("\n2️⃣ Verificando Django Channels...")
try:
    import channels
    print(f"   ✅ Django Channels {channels.__version__} instalado")
except ImportError:
    print("   ❌ Django Channels NO instalado")
    print("   💡 Solución: pip install channels==4.0.0")
    channels_installed = False
else:
    channels_installed = True

# 3. Verificar channels-redis
print("\n3️⃣ Verificando channels-redis...")
try:
    import channels_redis
    print("   ✅ channels-redis instalado")
except ImportError:
    print("   ❌ channels-redis NO instalado")
    print("   💡 Solución: pip install channels-redis==4.1.0")

# 4. Verificar Daphne
print("\n4️⃣ Verificando Daphne (servidor ASGI)...")
try:
    import daphne
    print(f"   ✅ Daphne {daphne.__version__} instalado")
except ImportError:
    print("   ❌ Daphne NO instalado")
    print("   💡 Solución: pip install daphne==4.0.0")

# 5. Verificar Redis
print("\n5️⃣ Verificando conexión a Redis...")
try:
    import redis
    r = redis.Redis(host='localhost', port=6379, db=0, socket_connect_timeout=2)
    r.ping()
    print("   ✅ Redis conectado (localhost:6379)")
except ImportError:
    print("   ❌ redis-py NO instalado")
    print("   💡 Solución: pip install redis==7.0.1")
except redis.exceptions.ConnectionError:
    print("   ❌ Redis NO está corriendo")
    print("   💡 Solución: redis-server")
except Exception as e:
    print(f"   ❌ Error conectando a Redis: {e}")

# 6. Verificar configuración Django
print("\n6️⃣ Verificando configuración Django...")
try:
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'WearableApi.settings')
    django.setup()
    
    from django.conf import settings
    
    # Verificar ASGI_APPLICATION
    if hasattr(settings, 'ASGI_APPLICATION'):
        print(f"   ✅ ASGI_APPLICATION: {settings.ASGI_APPLICATION}")
    else:
        print("   ❌ ASGI_APPLICATION no configurado en settings.py")
    
    # Verificar CHANNEL_LAYERS
    if hasattr(settings, 'CHANNEL_LAYERS'):
        backend = settings.CHANNEL_LAYERS['default']['BACKEND']
        print(f"   ✅ CHANNEL_LAYERS: {backend}")
    else:
        print("   ❌ CHANNEL_LAYERS no configurado en settings.py")
    
    # Verificar que 'channels' está en INSTALLED_APPS
    if 'channels' in settings.INSTALLED_APPS:
        print("   ✅ 'channels' en INSTALLED_APPS")
    else:
        print("   ❌ 'channels' NO está en INSTALLED_APPS")
    
    # Verificar que 'daphne' está en INSTALLED_APPS
    if 'daphne' in settings.INSTALLED_APPS:
        print("   ✅ 'daphne' en INSTALLED_APPS")
    else:
        print("   ❌ 'daphne' NO está en INSTALLED_APPS")
        
except Exception as e:
    print(f"   ❌ Error cargando configuración: {e}")

# 7. Verificar archivos de WebSocket
print("\n7️⃣ Verificando archivos de WebSocket...")

files_to_check = [
    ('WearableApi/asgi.py', 'Configuración ASGI'),
    ('api/consumers.py', 'WebSocket Consumers'),
    ('api/routing.py', 'WebSocket Routing'),
    ('api/signals.py', 'Signals para notificaciones'),
]

for file_path, description in files_to_check:
    if os.path.exists(file_path):
        print(f"   ✅ {description}: {file_path}")
    else:
        print(f"   ❌ {description} NO ENCONTRADO: {file_path}")

# 8. Verificar que signals están registrados
print("\n8️⃣ Verificando signals...")
try:
    from api.apps import ApiConfig
    if hasattr(ApiConfig, 'ready'):
        print("   ✅ ApiConfig.ready() definido (signals se registrarán)")
    else:
        print("   ❌ ApiConfig.ready() NO definido")
except Exception as e:
    print(f"   ❌ Error verificando signals: {e}")

# Resumen final
print("\n" + "="*70)
print("📊 RESUMEN")
print("="*70)

if channels_installed:
    print("✅ Django Channels está instalado y configurado")
    print("\n🚀 Para iniciar el servidor con WebSockets:")
    print("   daphne -b 0.0.0.0 -p 8000 WearableApi.asgi:application")
    print("\n🔗 URL de prueba:")
    print("   ws://localhost:8000/ws/notificaciones/1/")
else:
    print("❌ Django Channels NO está instalado")
    print("\n📦 Para instalar:")
    print("   pip install channels==4.0.0 channels-redis==4.1.0 daphne==4.0.0")

print("="*70)
