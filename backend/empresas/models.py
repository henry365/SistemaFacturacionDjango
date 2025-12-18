from django.db import models
from django.core.exceptions import ValidationError
import uuid

class Empresa(models.Model):
    nombre = models.CharField(max_length=200)
    rnc = models.CharField(max_length=50, unique=True, db_index=True)
    direccion = models.TextField(blank=True, null=True)
    telefono = models.CharField(max_length=20, blank=True, null=True)
    logo = models.ImageField(upload_to='logos/', blank=True, null=True)
    configuracion_fiscal = models.JSONField(default=dict, blank=True, help_text="Secuencias de NCF y otras configuraciones fiscales")
    activo = models.BooleanField(default=True, db_index=True)
    uuid = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)
    fecha_creacion = models.DateTimeField(auto_now_add=True)
    fecha_actualizacion = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Empresa'
        verbose_name_plural = 'Empresas'
        ordering = ['nombre']
        indexes = [
            models.Index(fields=['activo', 'nombre']),
            models.Index(fields=['-fecha_creacion']),
        ]

    def clean(self):
        """Validaciones a nivel de modelo"""
        if self.nombre:
            self.nombre = self.nombre.strip()
            if not self.nombre:
                raise ValidationError({'nombre': 'El nombre no puede estar vacío.'})
        
        if self.rnc:
            self.rnc = self.rnc.strip()
            if not self.rnc:
                raise ValidationError({'rnc': 'El RNC no puede estar vacío.'})

    def __str__(self):
        return self.nombre
