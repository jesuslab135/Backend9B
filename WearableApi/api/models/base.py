
from django.db import models

class TimeStampedModel(models.Model):
    
    created_at = models.DateTimeField(
        auto_now_add=True,
        help_text="Timestamp when the record was created"
    )
    updated_at = models.DateTimeField(
        auto_now=True,
        help_text="Timestamp when the record was last updated"
    )
    
    class Meta:
        abstract = True
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.__class__.__name__} (ID: {self.pk})"

class SoftDeleteModel(TimeStampedModel):
    
    is_deleted = models.BooleanField(
        default=False,
        help_text="Flag indicating if record is soft-deleted"
    )
    deleted_at = models.DateTimeField(
        null=True,
        blank=True,
        help_text="Timestamp when record was soft-deleted"
    )
    
    class Meta:
        abstract = True
    
    def delete(self, using=None, keep_parents=False):
        from django.utils import timezone
        self.is_deleted = True
        self.deleted_at = timezone.now()
        self.save(using=using)
    
    def hard_delete(self):
        super().delete()
    
    def restore(self):
        self.is_deleted = False
        self.deleted_at = None
        self.save()

class SoftDeleteManager(models.Manager):
    
    def get_queryset(self):
        return super().get_queryset().filter(is_deleted=False)
    
    def active(self):
        return self.get_queryset()
    
    def deleted(self):
        return super().get_queryset().filter(is_deleted=True)
    
    def all_with_deleted(self):
        return super().get_queryset()

