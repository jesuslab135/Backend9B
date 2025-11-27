"""
Script para limpiar datos antiguos y reentrenar modelo SIN data leakage
"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'WearableApi.settings')
django.setup()

from api.models import Lectura, Ventana, Analisis

print("🧹 Limpiando datos antiguos...")
print(f"   Lecturas: {Lectura.objects.count()}")
print(f"   Ventanas: {Ventana.objects.count()}")
print(f"   Análisis: {Analisis.objects.count()}")

# Eliminar TODO para empezar con datos frescos
Analisis.objects.all().delete()
Lectura.objects.all().delete()
Ventana.objects.all().delete()

print("✅ Datos limpiados completamente!")
print("\n🔄 Ejecutando train_model.py con datos limpios...")

import subprocess
import sys

result = subprocess.run(
    [sys.executable, "train_model.py", "--auto"],
    cwd=os.path.dirname(os.path.abspath(__file__))
)

sys.exit(result.returncode)
