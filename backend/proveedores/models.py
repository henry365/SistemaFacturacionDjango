from django.db import models
from django.conf import settings
from django.core.exceptions import ValidationError
import uuid

class Proveedor(models.Model):
    empresa = models.ForeignKey('empresas.Empresa', on_delete=models.PROTECT, related_name='proveedores', null=True, blank=True, db_index=True)
    uuid = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)
    TIPO_IDENTIFICACION_CHOICES = (
        ('RNC', 'RNC'),
        ('CEDULA', 'Cédula'),
        ('PASAPORTE', 'Pasaporte'),
        ('OTRO', 'Otro'),
    )

    TIPO_CONTRIBUYENTE_CHOICES = (
        ('JURIDICA', 'Persona Jurídica'),
        ('FISICA', 'Persona Física'),
        ('INFORMAL', 'Proveedor Informal'),
        ('ESTATAL', 'Gobierno / Estatal'),
        ('EXTRANJERO', 'Extranjero'),
    )

    nombre = models.CharField(max_length=200)
    tipo_identificacion = models.CharField(
        max_length=20, 
        choices=TIPO_IDENTIFICACION_CHOICES,
        blank=True, 
        null=True,
        db_index=True
    )
    numero_identificacion = models.CharField(max_length=50, blank=True, null=True, db_index=True)
    
    tipo_contribuyente = models.CharField(
        max_length=20, 
        choices=TIPO_CONTRIBUYENTE_CHOICES, 
        default='JURIDICA',
        db_index=True,
        help_text="Determina las reglas de retención (DGII)"
    )
    
    telefono = models.CharField(max_length=20, blank=True, null=True)
    correo_electronico = models.EmailField(blank=True, null=True)
    direccion = models.TextField(blank=True, null=True)
    es_internacional = models.BooleanField(default=False)
    activo = models.BooleanField(default=True, db_index=True)
    fecha_creacion = models.DateTimeField(auto_now_add=True)
    fecha_actualizacion = models.DateTimeField(auto_now=True)
    usuario_creacion = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name='proveedores_creados', null=True, blank=True)
    usuario_modificacion = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name='proveedores_modificados', null=True, blank=True)
    idempotency_key = models.CharField(max_length=100, unique=True, blank=True, null=True)

    class Meta:
        verbose_name = 'Proveedor'
        verbose_name_plural = 'Proveedores'
        ordering = ['nombre']
        unique_together = ('empresa', 'numero_identificacion')
        indexes = [
            models.Index(fields=['empresa', 'activo']),
            models.Index(fields=['empresa', 'tipo_identificacion', 'numero_identificacion']),
            models.Index(fields=['tipo_contribuyente', 'activo']),
            models.Index(fields=['-fecha_creacion']),
        ]

    def clean(self):
        """Validaciones a nivel de modelo"""
        if self.nombre:
            self.nombre = self.nombre.strip()
            if not self.nombre:
                raise ValidationError({'nombre': 'El nombre no puede estar vacío.'})
        
        # Validar que RNC requiere numero_identificacion
        if self.tipo_identificacion == 'RNC' and not self.numero_identificacion:
            raise ValidationError({'numero_identificacion': 'El número de identificación es obligatorio para RNC.'})
        
        if self.correo_electronico:
            self.correo_electronico = self.correo_electronico.strip().lower()

    @property
    def tipo_identificacion_display(self):
        """Obtener el display del tipo de identificación"""
        return self.get_tipo_identificacion_display() if self.tipo_identificacion else None
    
    @property
    def tipo_contribuyente_display(self):
        """Obtener el display del tipo de contribuyente"""
        return self.get_tipo_contribuyente_display()

    def __str__(self):
        identificacion = f" ({self.numero_identificacion})" if self.numero_identificacion else ""
        return f"{self.nombre}{identificacion}"
