from django.db import models
from django.conf import settings
from django.core.validators import MinValueValidator, MaxValueValidator
from django.core.exceptions import ValidationError
import uuid

class Vendedor(models.Model):
    empresa = models.ForeignKey('empresas.Empresa', on_delete=models.PROTECT, related_name='vendedores', null=True, blank=True, db_index=True)
    uuid = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)
    nombre = models.CharField(max_length=200)
    cedula = models.CharField(max_length=20, blank=True, null=True, db_index=True)
    telefono = models.CharField(max_length=20, blank=True, null=True)
    correo = models.EmailField(blank=True, null=True)
    comision_porcentaje = models.DecimalField(
        max_digits=5, 
        decimal_places=2, 
        default=0.00,
        validators=[MinValueValidator(0), MaxValueValidator(100)],
        help_text="Porcentaje de comisión por ventas (0-100)"
    )
    usuario = models.OneToOneField(
        settings.AUTH_USER_MODEL, 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True,
        related_name='vendedor_perfil',
        db_index=True,
        help_text="Usuario del sistema asociado a este vendedor (opcional)"
    )
    activo = models.BooleanField(default=True, db_index=True)
    fecha_creacion = models.DateTimeField(auto_now_add=True)
    fecha_actualizacion = models.DateTimeField(auto_now=True)
    usuario_creacion = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name='vendedores_creados', null=True, blank=True)
    usuario_modificacion = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name='vendedores_modificados', null=True, blank=True)
    idempotency_key = models.CharField(max_length=100, unique=True, blank=True, null=True)

    class Meta:
        verbose_name = 'Vendedor'
        verbose_name_plural = 'Vendedores'
        ordering = ['nombre']
        unique_together = ('empresa', 'cedula')
        indexes = [
            models.Index(fields=['empresa', 'activo']),
            models.Index(fields=['empresa', 'cedula']),
            models.Index(fields=['-fecha_creacion']),
        ]

    def clean(self):
        """Validaciones a nivel de modelo"""
        if self.nombre:
            self.nombre = self.nombre.strip()
            if not self.nombre:
                raise ValidationError({'nombre': 'El nombre no puede estar vacío.'})
        
        if self.comision_porcentaje < 0 or self.comision_porcentaje > 100:
            raise ValidationError({'comision_porcentaje': 'La comisión debe estar entre 0 y 100.'})
        
        if self.correo:
            self.correo = self.correo.strip().lower()
        
        # Validar que usuario pertenezca a la misma empresa si ambos están asignados
        if self.usuario and self.empresa and hasattr(self.usuario, 'empresa') and self.usuario.empresa != self.empresa:
            raise ValidationError({'usuario': 'El usuario debe pertenecer a la misma empresa del vendedor.'})

    def __str__(self):
        return f"{self.nombre} ({self.empresa.nombre if self.empresa else 'Sin empresa'})"
