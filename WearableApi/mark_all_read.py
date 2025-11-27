"""
Script para marcar todas las notificaciones como leídas
Útil para limpiar notificaciones viejas después de reiniciar el sistema
"""

import os
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'WearableApi.settings')
django.setup()

from api.models import Notificacion, Consumidor

def mark_all_notifications_read(consumidor_id=None):
    """
    Marca todas las notificaciones como leídas
    
    Args:
        consumidor_id: Si se proporciona, solo marca las de ese consumidor
    """
    if consumidor_id:
        notificaciones = Notificacion.objects.filter(
            consumidor_id=consumidor_id,
            leida=False
        )
        print(f"📋 Encontradas {notificaciones.count()} notificaciones no leídas para consumidor {consumidor_id}")
    else:
        notificaciones = Notificacion.objects.filter(leida=False)
        print(f"📋 Encontradas {notificaciones.count()} notificaciones no leídas en total")
    
    if notificaciones.count() == 0:
        print("✅ No hay notificaciones pendientes")
        return
    
    # Mostrar resumen por consumidor
    print("\n📊 Resumen por consumidor:")
    for consumidor in Consumidor.objects.all():
        count = notificaciones.filter(consumidor=consumidor).count()
        if count > 0:
            print(f"   - {consumidor.usuario.nombre} ({consumidor.usuario.email}): {count} notificaciones")
    
    # Confirmar
    respuesta = input(f"\n¿Marcar todas como leídas? (s/n): ")
    
    if respuesta.lower() in ['s', 'si', 'y', 'yes']:
        # Marcar todas como leídas usando update masivo (más eficiente)
        updated = notificaciones.update(leida=True)
        print(f"\n✅ {updated} notificaciones marcadas como leídas")
    else:
        print("\n❌ Operación cancelada")


def show_notification_stats():
    """Muestra estadísticas de notificaciones"""
    total = Notificacion.objects.count()
    leidas = Notificacion.objects.filter(leida=True).count()
    no_leidas = Notificacion.objects.filter(leida=False).count()
    
    print("\n" + "="*60)
    print("📊 ESTADÍSTICAS DE NOTIFICACIONES")
    print("="*60)
    print(f"Total:      {total}")
    print(f"Leídas:     {leidas} ({leidas/total*100:.1f}%)" if total > 0 else "Leídas:     0")
    print(f"No leídas:  {no_leidas} ({no_leidas/total*100:.1f}%)" if total > 0 else "No leídas:  0")
    print("="*60 + "\n")


if __name__ == "__main__":
    print("\n" + "="*60)
    print("🔔 SCRIPT DE LIMPIEZA DE NOTIFICACIONES")
    print("="*60 + "\n")
    
    show_notification_stats()
    
    # Preguntar qué hacer
    print("Opciones:")
    print("1. Marcar todas las notificaciones como leídas")
    print("2. Marcar solo las de un consumidor específico")
    print("3. Ver estadísticas y salir")
    
    opcion = input("\nSelecciona una opción (1-3): ")
    
    if opcion == "1":
        mark_all_notifications_read()
    elif opcion == "2":
        # Listar consumidores
        print("\n📋 Consumidores disponibles:")
        consumidores = Consumidor.objects.select_related('usuario').all()
        for c in consumidores:
            unread_count = Notificacion.objects.filter(
                consumidor=c, 
                leida=False
            ).count()
            print(f"   ID {c.id}: {c.usuario.nombre} ({c.usuario.email}) - {unread_count} no leídas")
        
        consumidor_id = input("\nIngresa el ID del consumidor: ")
        try:
            consumidor_id = int(consumidor_id)
            mark_all_notifications_read(consumidor_id)
        except ValueError:
            print("❌ ID inválido")
    elif opcion == "3":
        print("\n👋 Saliendo...")
    else:
        print("\n❌ Opción inválida")
    
    # Mostrar estadísticas finales
    show_notification_stats()
