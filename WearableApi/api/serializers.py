"""
API Serializers
===============
Serializers for all models to convert between Python objects and JSON.

Design Pattern: Data Transfer Object (DTO)
Serializers act as DTOs for API communication.
"""

from rest_framework import serializers
from api.models import *


# ============================================
# USER SERIALIZERS
# ============================================

class UsuarioSerializer(serializers.ModelSerializer):
    """
    Usuario serializer with password handling.
    Never expose password_hash in responses.
    """
    
    password = serializers.CharField(
        write_only=True,
        required=True,
        style={'input_type': 'password'}
    )
    
    class Meta:
        model = Usuario
        fields = [
            'id', 'nombre', 'telefono', 'email', 'password', 
            'rol', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']
        extra_kwargs = {
            'password_hash': {'write_only': True}
        }
    
    def create(self, validated_data):
        """Create user with hashed password"""
        password = validated_data.pop('password')
        usuario = Usuario(**validated_data)
        usuario.set_password(password)
        usuario.save()
        return usuario
    
    def update(self, instance, validated_data):
        """Update user, hash password if provided"""
        password = validated_data.pop('password', None)
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        
        if password:
            instance.set_password(password)
        
        instance.save()
        return instance


class AdministradorSerializer(serializers.ModelSerializer):
    """Administrador serializer with nested usuario"""
    
    usuario = UsuarioSerializer(read_only=True)
    usuario_id = serializers.PrimaryKeyRelatedField(
        queryset=Usuario.objects.all(),
        source='usuario',
        write_only=True
    )
    
    class Meta:
        model = Administrador
        fields = ['id', 'usuario', 'usuario_id', 'area_responsable', 'created_at', 'updated_at']
        read_only_fields = ['id', 'created_at', 'updated_at']


class ConsumidorSerializer(serializers.ModelSerializer):
    """Consumidor serializer with nested usuario and BMI"""
    
    usuario = UsuarioSerializer(read_only=True)
    usuario_id = serializers.PrimaryKeyRelatedField(
        queryset=Usuario.objects.all(),
        source='usuario',
        write_only=True
    )
    bmi_category = serializers.ReadOnlyField()
    
    class Meta:
        model = Consumidor
        fields = [
            'id', 'usuario', 'usuario_id', 'edad', 'peso', 'altura', 
            'bmi', 'bmi_category', 'genero', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'bmi', 'bmi_category', 'created_at', 'updated_at']


# ============================================
# LOOKUP SERIALIZERS
# ============================================

class EmocionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Emocion
        fields = '__all__'
        read_only_fields = ['id', 'created_at', 'updated_at']


class MotivoSerializer(serializers.ModelSerializer):
    class Meta:
        model = Motivo
        fields = '__all__'
        read_only_fields = ['id', 'created_at', 'updated_at']


class SolucionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Solucion
        fields = '__all__'
        read_only_fields = ['id', 'created_at', 'updated_at']


class HabitoSerializer(serializers.ModelSerializer):
    class Meta:
        model = Habito
        fields = '__all__'
        read_only_fields = ['id', 'created_at', 'updated_at']


class PermisoSerializer(serializers.ModelSerializer):
    is_readonly = serializers.ReadOnlyField()
    is_full_access = serializers.ReadOnlyField()
    
    class Meta:
        model = Permiso
        fields = '__all__'
        read_only_fields = ['id', 'created_at', 'updated_at']


# ============================================
# FORM SERIALIZERS
# ============================================

class FormularioSerializer(serializers.ModelSerializer):
    """Formulario serializer with JSONB validation"""
    
    habito_nombre = serializers.CharField(source='habito.nombre', read_only=True)
    consumidor_nombre = serializers.CharField(source='consumidor.nombre', read_only=True)
    emotion_count = serializers.ReadOnlyField()
    motive_count = serializers.ReadOnlyField()
    solution_count = serializers.ReadOnlyField()
    
    class Meta:
        model = Formulario
        fields = [
            'id', 'consumidor', 'consumidor_nombre', 'fecha_envio', 
            'habito', 'habito_nombre', 'emociones', 'motivos', 'soluciones',
            'emotion_count', 'motive_count', 'solution_count',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'fecha_envio', 'created_at', 'updated_at']


class FormularioTemporalSerializer(serializers.ModelSerializer):
    """FormularioTemporal serializer"""
    
    consumidor_nombre = serializers.CharField(source='consumidor.nombre', read_only=True)
    emotion_count = serializers.ReadOnlyField()
    
    class Meta:
        model = FormularioTemporal
        fields = [
            'id', 'consumidor', 'consumidor_nombre', 'emociones',
            'emotion_count', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']


# ============================================
# SENSOR SERIALIZERS
# ============================================

class VentanaSerializer(serializers.ModelSerializer):
    """Ventana serializer with computed properties"""
    
    consumidor_nombre = serializers.CharField(source='consumidor.nombre', read_only=True)
    duration_minutes = serializers.ReadOnlyField()
    has_sensor_data = serializers.ReadOnlyField()
    has_embeddings = serializers.ReadOnlyField()
    
    class Meta:
        model = Ventana
        fields = [
            'id', 'consumidor', 'consumidor_nombre', 'window_start', 'window_end',
            'hr_mean', 'hr_std', 'gyro_energy', 'accel_energy',
            'emotion_embedding', 'motive_embedding', 'solution_embedding',
            'duration_minutes', 'has_sensor_data', 'has_embeddings',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']


class LecturaSerializer(serializers.ModelSerializer):
    """Lectura serializer with sensor data"""
    
    has_heart_rate = serializers.ReadOnlyField()
    has_accelerometer = serializers.ReadOnlyField()
    has_gyroscope = serializers.ReadOnlyField()
    
    class Meta:
        model = Lectura
        fields = [
            'id', 'ventana', 'heart_rate', 
            'accel_x', 'accel_y', 'accel_z',
            'gyro_x', 'gyro_y', 'gyro_z',
            'has_heart_rate', 'has_accelerometer', 'has_gyroscope',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']


# ============================================
# ANALYSIS SERIALIZERS
# ============================================

class AnalisisSerializer(serializers.ModelSerializer):
    """Analisis serializer with prediction details"""
    
    is_urge_predicted = serializers.ReadOnlyField()
    confidence_level = serializers.ReadOnlyField()
    consumidor_id = serializers.IntegerField(source='ventana.consumidor.id', read_only=True)
    
    class Meta:
        model = Analisis
        fields = [
            'id', 'ventana', 'consumidor_id', 'modelo_usado', 'probabilidad_modelo',
            'urge_label', 'recall', 'f1_score', 'accuracy', 'roc_auc',
            'comentario_modelo', 'feature_importance',
            'is_urge_predicted', 'confidence_level',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']


class DeseoSerializer(serializers.ModelSerializer):
    """Deseo serializer with resolution tracking"""
    
    consumidor_nombre = serializers.CharField(source='consumidor.nombre', read_only=True)
    is_active = serializers.ReadOnlyField()
    time_to_resolution = serializers.ReadOnlyField()
    
    class Meta:
        model = Deseo
        fields = [
            'id', 'consumidor', 'consumidor_nombre', 'ventana', 'tipo',
            'resolved', 'is_active', 'time_to_resolution',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']


class NotificacionSerializer(serializers.ModelSerializer):
    """Notificacion serializer with read status"""
    
    consumidor_nombre = serializers.CharField(source='consumidor.nombre', read_only=True)
    is_unread = serializers.ReadOnlyField()
    age_hours = serializers.ReadOnlyField()
    is_recent = serializers.ReadOnlyField()
    
    class Meta:
        model = Notificacion
        fields = [
            'id', 'consumidor', 'consumidor_nombre', 'deseo', 'tipo',
            'contenido', 'fecha_envio', 'leida',
            'is_unread', 'age_hours', 'is_recent',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'fecha_envio', 'created_at', 'updated_at']


# ============================================
# DASHBOARD SERIALIZERS (Read-Only)
# ============================================

class VwHabitTrackingSerializer(serializers.ModelSerializer):
    class Meta:
        model = VwHabitTracking
        fields = '__all__'


class VwHabitStatsSerializer(serializers.ModelSerializer):
    class Meta:
        model = VwHabitStats
        fields = '__all__'


class VwHeartRateTimelineSerializer(serializers.ModelSerializer):
    class Meta:
        model = VwHeartRateTimeline
        fields = '__all__'


class VwHeartRateStatsSerializer(serializers.ModelSerializer):
    class Meta:
        model = VwHeartRateStats
        fields = '__all__'


class VwPredictionTimelineSerializer(serializers.ModelSerializer):
    class Meta:
        model = VwPredictionTimeline
        fields = '__all__'


class VwPredictionSummarySerializer(serializers.ModelSerializer):
    class Meta:
        model = VwPredictionSummary
        fields = '__all__'


class VwDesiresTrackingSerializer(serializers.ModelSerializer):
    class Meta:
        model = VwDesiresTracking
        fields = '__all__'


class VwDesiresStatsSerializer(serializers.ModelSerializer):
    class Meta:
        model = VwDesiresStats
        fields = '__all__'


class VwDailySummarySerializer(serializers.ModelSerializer):
    class Meta:
        model = VwDailySummary
        fields = '__all__'


class VwWeeklyComparisonSerializer(serializers.ModelSerializer):
    class Meta:
        model = VwWeeklyComparison
        fields = '__all__'


# ============================================
# AUTH SERIALIZERS
# ============================================

class LoginSerializer(serializers.Serializer):
    """Serializer for login endpoint"""
    
    email = serializers.EmailField()
    password = serializers.CharField(style={'input_type': 'password'})


class RegisterSerializer(serializers.Serializer):
    """Serializer for user registration"""
    
    nombre = serializers.CharField(max_length=100)
    email = serializers.EmailField()
    password = serializers.CharField(
        min_length=6,
        style={'input_type': 'password'}
    )
    telefono = serializers.CharField(max_length=20, required=False, allow_blank=True)
    rol = serializers.ChoiceField(choices=RolChoices.choices, default='consumidor')
    
    # Consumidor specific fields (optional)
    edad = serializers.IntegerField(required=False, allow_null=True)
    peso = serializers.FloatField(required=False, allow_null=True)
    altura = serializers.FloatField(required=False, allow_null=True)
    genero = serializers.ChoiceField(choices=GeneroChoices.choices, required=False)
    
    # Administrador specific fields (optional)
    area_responsable = serializers.CharField(max_length=100, required=False, allow_blank=True)
    
    def validate_email(self, value):
        """Check if email already exists"""
        if Usuario.objects.filter(email=value).exists():
            raise serializers.ValidationError("Email already registered")
        return value