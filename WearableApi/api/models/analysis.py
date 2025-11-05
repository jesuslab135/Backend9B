
from django.db import models
from .base import TimeStampedModel
from .user import Consumidor
from .sensor import Ventana

class Analisis(TimeStampedModel):
    
    ventana = models.ForeignKey(
        Ventana,
        on_delete=models.CASCADE,
        related_name='analisis',
        help_text="Time window this analysis is based on"
    )
    modelo_usado = models.CharField(
        max_length=100,
        null=True,
        blank=True,
        help_text="Name/version of ML model used"
    )
    probabilidad_modelo = models.FloatField(
        null=True,
        blank=True,
        help_text="Model prediction probability (0-1)"
    )
    urge_label = models.IntegerField(
        null=True,
        blank=True,
        help_text="Binary label: 1=urge detected, 0=no urge"
    )
    recall = models.FloatField(
        null=True,
        blank=True,
        help_text="Model recall metric (0-1)"
    )
    f1_score = models.FloatField(
        null=True,
        blank=True,
        help_text="Model F1 score (0-1)"
    )
    accuracy = models.FloatField(
        null=True,
        blank=True,
        help_text="Model accuracy (0-1)"
    )
    roc_auc = models.FloatField(
        null=True,
        blank=True,
        help_text="ROC AUC score (0-1)"
    )
    comentario_modelo = models.TextField(
        null=True,
        blank=True,
        help_text="Optional notes about the prediction"
    )
    feature_importance = models.JSONField(
        null=True,
        blank=True,
        help_text="Feature importance scores (JSONB)"
    )
    
    class Meta:
        db_table = 'analisis'
        verbose_name = 'Análisis'
        verbose_name_plural = 'Análisis'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['ventana']),
            models.Index(fields=['probabilidad_modelo']),
        ]
        constraints = [
            models.CheckConstraint(
                check=models.Q(urge_label__in=[0, 1]),
                name='check_urge_label'
            ),
            models.CheckConstraint(
                check=models.Q(probabilidad_modelo__gte=0, probabilidad_modelo__lte=1),
                name='check_probabilidad_range'
            ),
        ]
    
    def __str__(self):
        urge_str = "Urge" if self.urge_label == 1 else "No Urge"
        return f"Analysis {self.id} - {urge_str} (p={self.probabilidad_modelo})"
    
    @property
    def is_urge_predicted(self):
        return self.urge_label == 1
    
    @property
    def confidence_level(self):
        if self.probabilidad_modelo is None:
            return "Unknown"
        
        if self.probabilidad_modelo < 0.6:
            return "Low"
        elif self.probabilidad_modelo < 0.8:
            return "Medium"
        else:
            return "High"
    
    @property
    def consumidor(self):
        return self.ventana.consumidor if self.ventana else None

class DeseoTipoChoices(models.TextChoices):
    COMIDA = 'comida', 'Comida'
    BEBIDA = 'bebida', 'Bebida'
    COMPRA = 'compra', 'Compra'
    SUSTANCIA = 'sustancia', 'Sustancia'
    OTRO = 'otro', 'Otro'

class Deseo(TimeStampedModel):
    
    consumidor = models.ForeignKey(
        Consumidor,
        on_delete=models.CASCADE,
        related_name='deseos',
        help_text="Consumer experiencing the desire"
    )
    ventana = models.ForeignKey(
        Ventana,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='deseos',
        help_text="Associated time window (optional)"
    )
    tipo = models.CharField(
        max_length=50,
        choices=DeseoTipoChoices.choices,
        help_text="Type of desire/urge"
    )
    resolved = models.BooleanField(
        default=False,
        help_text="Whether the desire was resolved/overcome"
    )
    
    class Meta:
        db_table = 'deseos'
        verbose_name = 'Deseo'
        verbose_name_plural = 'Deseos'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['consumidor', 'created_at']),
            models.Index(fields=['consumidor', 'resolved']),
            models.Index(fields=['ventana']),
        ]
    
    def __str__(self):
        status = "Resuelto" if self.resolved else "Activo"
        return f"Desire {self.id} - {self.tipo} ({status})"
    
    @property
    def is_active(self):
        return not self.resolved
    
    @property
    def time_to_resolution(self):
        if self.resolved and self.created_at and self.updated_at:
            delta = self.updated_at - self.created_at
            return round(delta.total_seconds() / 3600, 2)
        return None
    
    def mark_resolved(self):
        self.resolved = True
        self.save()

class NotificacionTipoChoices(models.TextChoices):
    RECOMENDACION = 'recomendacion', 'Recomendación'
    ALERTA = 'alerta', 'Alerta'
    RECORDATORIO = 'recordatorio', 'Recordatorio'
    LOGRO = 'logro', 'Logro'

class Notificacion(TimeStampedModel):
    
    consumidor = models.ForeignKey(
        Consumidor,
        on_delete=models.CASCADE,
        related_name='notificaciones',
        help_text="Consumer receiving the notification"
    )
    deseo = models.ForeignKey(
        Deseo,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='notificaciones',
        help_text="Related desire (optional)"
    )
    tipo = models.CharField(
        max_length=50,
        choices=NotificacionTipoChoices.choices,
        help_text="Type of notification"
    )
    contenido = models.TextField(
        help_text="Notification content/message"
    )
    fecha_envio = models.DateTimeField(
        auto_now_add=True,
        help_text="Timestamp when notification was sent"
    )
    leida = models.BooleanField(
        default=False,
        help_text="Whether notification has been read"
    )
    
    class Meta:
        db_table = 'notificaciones'
        verbose_name = 'Notificación'
        verbose_name_plural = 'Notificaciones'
        ordering = ['-fecha_envio']
        indexes = [
            models.Index(fields=['consumidor', 'fecha_envio']),
            models.Index(fields=['consumidor', 'leida']),
            models.Index(fields=['deseo']),
            models.Index(fields=['fecha_envio']),
        ]
    
    def __str__(self):
        status = "Leída" if self.leida else "No leída"
        return f"Notification {self.id} - {self.tipo} ({status})"
    
    @property
    def is_unread(self):
        return not self.leida
    
    def mark_read(self):
        self.leida = True
        self.save()
    
    def mark_unread(self):
        self.leida = False
        self.save()
    
    @property
    def age_hours(self):
        from django.utils import timezone
        if self.fecha_envio:
            delta = timezone.now() - self.fecha_envio
            return round(delta.total_seconds() / 3600, 2)
        return None
    
    @property
    def is_recent(self):
        age = self.age_hours
        return age is not None and age < 24

