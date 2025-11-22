#!/usr/bin/env python
"""
Script para desactivar todas las simulaciones por defecto
Ejecutar con: python manage.py shell < disable_simulations.py
O desde Docker: docker exec -it wearable-django python manage.py shell < disable_simulations.py
"""

from api.models import Consumidor

# Desactivar todas las simulaciones
count = Consumidor.objects.all().update(is_simulating=False)

print(f"✅ {count} consumidores actualizados")
print("✅ Todas las simulaciones han sido DESACTIVADAS")
print("💡 Los administradores pueden activarlas desde el frontend con el switch toggle")
