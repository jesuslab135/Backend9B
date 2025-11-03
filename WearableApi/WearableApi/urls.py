"""
Main URL Configuration
======================
Root URL configuration including admin, API, and Swagger documentation.
"""

from django.contrib import admin
from django.urls import path, include
from drf_spectacular.views import (
    SpectacularAPIView,
    SpectacularSwaggerView,
    SpectacularRedocView,
)

def trigger_error(request):
    division_by_zero = 1 / 0

urlpatterns = [
    # Admin interface
    path('admin/', admin.site.urls),
    
    # API endpoints
    path('api/', include('api.urls')),
    
    # ============================================
    # API DOCUMENTATION (Swagger/OpenAPI)
    # ============================================
    
    # OpenAPI schema
    path('api/schema/', SpectacularAPIView.as_view(), name='schema'),
    
    # Swagger UI (interactive documentation)
    path('api/docs/', SpectacularSwaggerView.as_view(url_name='schema'), name='swagger-ui'),
    
    # ReDoc (alternative documentation UI)
    path('api/redoc/', SpectacularRedocView.as_view(url_name='schema'), name='redoc'),
]

"""
AVAILABLE URLS
==============

ADMIN PANEL
-----------
http://localhost:8000/admin/

API ROOT
--------
http://localhost:8000/api/

API DOCUMENTATION
-----------------
Swagger UI (Interactive):  http://localhost:8000/api/docs/
ReDoc (Alternative):       http://localhost:8000/api/redoc/
OpenAPI Schema (JSON):     http://localhost:8000/api/schema/

MAIN ENDPOINTS
--------------
Users:           http://localhost:8000/api/usuarios/
Register:        http://localhost:8000/api/usuarios/register/
Login:           http://localhost:8000/api/usuarios/login/
Consumers:       http://localhost:8000/api/consumidores/
Admins:          http://localhost:8000/api/administradores/

Lookup Tables:   http://localhost:8000/api/emociones/
                 http://localhost:8000/api/motivos/
                 http://localhost:8000/api/soluciones/
                 http://localhost:8000/api/habitos/

Forms:           http://localhost:8000/api/formularios/
                 http://localhost:8000/api/formularios-temporales/

Sensor Data:     http://localhost:8000/api/ventanas/
                 http://localhost:8000/api/lecturas/

Analysis:        http://localhost:8000/api/analisis/
                 http://localhost:8000/api/deseos/
                 http://localhost:8000/api/notificaciones/

Dashboard:       http://localhost:8000/api/dashboard/daily-summary/
                 http://localhost:8000/api/dashboard/habit-tracking/
                 http://localhost:8000/api/dashboard/heart-rate/
                 http://localhost:8000/api/dashboard/predictions/
                 http://localhost:8000/api/dashboard/desires/
"""