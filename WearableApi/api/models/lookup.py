
from django.db import models
from .base import TimeStampedModel

class BaseLookupModel(TimeStampedModel):
    
    nombre = models.CharField(
        max_length=50,
        unique=True,
        help_text="Unique name identifier"
    )
    descripcion = models.TextField(
        null=True,
        blank=True,
        help_text="Optional description"
    )
    
    class Meta:
        abstract = True
        ordering = ['nombre']
    
    def __str__(self):
        return self.nombre

class Emocion(BaseLookupModel):
    
    class Meta:
        db_table = 'emociones'
        verbose_name = 'Emoción'
        verbose_name_plural = 'Emociones'

class Motivo(BaseLookupModel):
    
    class Meta:
        db_table = 'motivos'
        verbose_name = 'Motivo'
        verbose_name_plural = 'Motivos'

class Solucion(BaseLookupModel):
    
    class Meta:
        db_table = 'soluciones'
        verbose_name = 'Solución'
        verbose_name_plural = 'Soluciones'

class Habito(BaseLookupModel):
    
    class Meta:
        db_table = 'habitos'
        verbose_name = 'Hábito'
        verbose_name_plural = 'Hábitos'

class Permiso(TimeStampedModel):
    
    lectura = models.BooleanField(
        default=True,
        help_text="Permission to read/view"
    )
    creacion = models.BooleanField(
        default=False,
        help_text="Permission to create"
    )
    edicion = models.BooleanField(
        default=False,
        help_text="Permission to edit"
    )
    eliminacion = models.BooleanField(
        default=False,
        help_text="Permission to delete"
    )
    
    class Meta:
        db_table = 'permisos'
        verbose_name = 'Permiso'
        verbose_name_plural = 'Permisos'
    
    def __str__(self):
        perms = []
        if self.lectura:
            perms.append('Lectura')
        if self.creacion:
            perms.append('Creación')
        if self.edicion:
            perms.append('Edición')
        if self.eliminacion:
            perms.append('Eliminación')
        return f"Permisos: {', '.join(perms) if perms else 'Ninguno'}"
    
    @property
    def is_readonly(self):
        return self.lectura and not (
            self.creacion or self.edicion or self.eliminacion
        )
    
    @property
    def is_full_access(self):
        return all([
            self.lectura,
            self.creacion,
            self.edicion,
            self.eliminacion
        ])

