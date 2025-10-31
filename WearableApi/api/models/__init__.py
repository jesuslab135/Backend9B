"""
API Models Package
==================
Centralizes all model imports for easy access.

Usage:
    from api.models import Usuario, Consumidor, Formulario
"""

# Base models
from .base import TimeStampedModel, SoftDeleteModel, SoftDeleteManager

# User models
from .user import (
    Usuario,
    Administrador,
    Consumidor,
    RolChoices,
    GeneroChoices
)

# Lookup models
from .lookup import (
    Emocion,
    Motivo,
    Solucion,
    Habito,
    Permiso
)

# Form models
from .form import (
    Formulario,
    FormularioTemporal
)

# Sensor models
from .sensor import (
    Ventana,
    Lectura
)

# Analysis models
from .analysis import (
    Analisis,
    Deseo,
    Notificacion,
    DeseoTipoChoices,
    NotificacionTipoChoices
)

# Dashboard view models (read-only)
from .dashboard import (
    VwHabitTracking,
    VwHabitStats,
    VwHeartRateTimeline,
    VwHeartRateStats,
    VwPredictionTimeline,
    VwPredictionSummary,
    VwDesiresTracking,
    VwDesiresStats,
    VwDailySummary,
    VwWeeklyComparison
)

# Export all models
__all__ = [
    # Base
    'TimeStampedModel',
    'SoftDeleteModel',
    'SoftDeleteManager',
    
    # Users
    'Usuario',
    'Administrador',
    'Consumidor',
    'RolChoices',
    'GeneroChoices',
    
    # Lookups
    'Emocion',
    'Motivo',
    'Solucion',
    'Habito',
    'Permiso',
    
    # Forms
    'Formulario',
    'FormularioTemporal',
    
    # Sensors
    'Ventana',
    'Lectura',
    
    # Analysis
    'Analisis',
    'Deseo',
    'Notificacion',
    'DeseoTipoChoices',
    'NotificacionTipoChoices',
    
    # Dashboard Views
    'VwHabitTracking',
    'VwHabitStats',
    'VwHeartRateTimeline',
    'VwHeartRateStats',
    'VwPredictionTimeline',
    'VwPredictionSummary',
    'VwDesiresTracking',
    'VwDesiresStats',
    'VwDailySummary',
    'VwWeeklyComparison',
]