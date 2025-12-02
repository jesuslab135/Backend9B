# Django shell
from api.models import Notificacion, Consumidor
from django.utils import timezone

# Obtener consumidor ID 22
c = Consumidor.objects.get(id=22)
print(f'Consumidor: {c.usuario.nombre} (ID: {c.id})')

# Crear notificación NO LEÍDA
Notificacion.objects.create(
    consumidor=c,
    tipo='logro',
    contenido='¡Logro desbloqueado! 7 dias consecutivos completados.',
    leida=False,
    fecha_envio=timezone.now()
)

print('✅ Notificacion creada para consumidor 22')
print('⏳ Espera 10 segundos en el frontend...')