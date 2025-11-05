
from django.db import models
from django.contrib.auth.hashers import make_password, check_password
from .base import TimeStampedModel

class RolChoices(models.TextChoices):
    CONSUMIDOR = 'consumidor', 'Consumidor'
    ADMINISTRADOR = 'administrador', 'Administrador'

class Usuario(TimeStampedModel):
    
    nombre = models.CharField(
        max_length=100,
        help_text="Full name of the user"
    )
    telefono = models.CharField(
        max_length=20,
        null=True,
        blank=True,
        help_text="Phone number (optional)"
    )
    email = models.EmailField(
        max_length=120,
        unique=True,
        help_text="Email address (used for login)"
    )
    password_hash = models.TextField(
        help_text="Hashed password (never store plain text)"
    )
    rol = models.CharField(
        max_length=50,
        choices=RolChoices.choices,
        default=RolChoices.CONSUMIDOR,
        help_text="User role (consumidor or administrador)"
    )
    
    class Meta:
        db_table = 'usuarios'
        verbose_name = 'Usuario'
        verbose_name_plural = 'Usuarios'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['email']),
            models.Index(fields=['rol']),
        ]
    
    def __str__(self):
        return f"{self.nombre} ({self.email})"
    
    def set_password(self, raw_password):
        self.password_hash = make_password(raw_password)
    
    def check_password(self, raw_password):
        return check_password(raw_password, self.password_hash)
    
    @property
    def is_administrador(self):
        return self.rol == RolChoices.ADMINISTRADOR
    
    @property
    def is_consumidor(self):
        return self.rol == RolChoices.CONSUMIDOR
    
    @property
    def is_authenticated(self):
        return True
    
    @property
    def is_active(self):
        return True
    
    @property
    def is_anonymous(self):
        return False

class Administrador(TimeStampedModel):
    
    usuario = models.OneToOneField(
        Usuario,
        on_delete=models.CASCADE,
        related_name='administrador',
        help_text="Reference to base Usuario"
    )
    area_responsable = models.CharField(
        max_length=100,
        null=True,
        blank=True,
        help_text="Responsible area (e.g., 'IT', 'Health Services')"
    )
    
    class Meta:
        db_table = 'administradores'
        verbose_name = 'Administrador'
        verbose_name_plural = 'Administradores'
        indexes = [
            models.Index(fields=['usuario']),
        ]
    
    def __str__(self):
        return f"Admin: {self.usuario.nombre}"
    
    @property
    def nombre(self):
        return self.usuario.nombre
    
    @property
    def email(self):
        return self.usuario.email

class GeneroChoices(models.TextChoices):
    MASCULINO = 'masculino', 'Masculino'
    FEMENINO = 'femenino', 'Femenino'

class Consumidor(TimeStampedModel):
    
    usuario = models.OneToOneField(
        Usuario,
        on_delete=models.CASCADE,
        related_name='consumidor',
        help_text="Reference to base Usuario"
    )
    edad = models.IntegerField(
        null=True,
        blank=True,
        help_text="Age in years"
    )
    peso = models.FloatField(
        null=True,
        blank=True,
        help_text="Weight in kilograms"
    )
    altura = models.FloatField(
        null=True,
        blank=True,
        help_text="Height in centimeters"
    )
    bmi = models.FloatField(
        null=True,
        blank=True,
        editable=False,
        help_text="Body Mass Index (calculated by database)"
    )
    genero = models.CharField(
        max_length=30,
        choices=GeneroChoices.choices,
        null=True,
        blank=True,
        help_text="Gender (optional)"
    )
    
    class Meta:
        db_table = 'consumidores'
        verbose_name = 'Consumidor'
        verbose_name_plural = 'Consumidores'
        indexes = [
            models.Index(fields=['usuario']),
        ]
    
    def __str__(self):
        return f"Consumer: {self.usuario.nombre}"
    
    @property
    def nombre(self):
        return self.usuario.nombre
    
    @property
    def email(self):
        return self.usuario.email
    
    def calculate_bmi(self):
        if self.peso and self.altura and self.altura > 0:
            altura_metros = self.altura / 100
            return round(self.peso / (altura_metros ** 2), 2)
        return None
    
    @property
    def bmi_category(self):
        if not self.bmi:
            return "Unknown"
        
        if self.bmi < 18.5:
            return "Underweight"
        elif self.bmi < 25:
            return "Normal"
        elif self.bmi < 30:
            return "Overweight"
        else:
            return "Obese"

