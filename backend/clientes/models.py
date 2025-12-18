from django.db import models
from django.conf import settings
from django.core.validators import MinValueValidator, MaxValueValidator
from django.core.exceptions import ValidationError
from vendedores.models import Vendedor
import uuid

class CategoriaCliente(models.Model):
    empresa = models.ForeignKey('empresas.Empresa', on_delete=models.PROTECT, related_name='categorias_cliente', null=True, blank=True, db_index=True)
    nombre = models.CharField(max_length=100)
    descripcion = models.TextField(blank=True, null=True)
    descuento_porcentaje = models.DecimalField(
        max_digits=5, decimal_places=2, default=0, 
        validators=[MinValueValidator(0), MaxValueValidator(100)],
        help_text="Descuento general para clientes de esta categoría"
    )
    uuid = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)
    activa = models.BooleanField(default=True, db_index=True)
    
    # Audit
    fecha_creacion = models.DateTimeField(auto_now_add=True)
    fecha_actualizacion = models.DateTimeField(auto_now=True)
    usuario_creacion = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name='categorias_cliente_creadas', null=True, blank=True)
    usuario_modificacion = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name='categorias_cliente_modificadas', null=True, blank=True)

    class Meta:
        verbose_name = 'Categoría de Cliente'
        verbose_name_plural = 'Categorías de Clientes'
        unique_together = ('empresa', 'nombre')
        ordering = ['nombre']
        indexes = [
            models.Index(fields=['empresa', 'activa']),
            models.Index(fields=['-fecha_creacion']),
        ]

    def clean(self):
        """Validaciones a nivel de modelo"""
        if self.nombre:
            self.nombre = self.nombre.strip()
            if not self.nombre:
                raise ValidationError({'nombre': 'El nombre no puede estar vacío.'})
        
        if self.descuento_porcentaje < 0 or self.descuento_porcentaje > 100:
            raise ValidationError({'descuento_porcentaje': 'El descuento debe estar entre 0 y 100.'})

    def __str__(self):
        return f"{self.nombre} ({self.empresa.nombre if self.empresa else 'Sin empresa'})"

class Cliente(models.Model):
    empresa = models.ForeignKey('empresas.Empresa', on_delete=models.PROTECT, related_name='clientes', null=True, blank=True, db_index=True)
    categoria = models.ForeignKey(CategoriaCliente, on_delete=models.SET_NULL, null=True, blank=True, related_name='clientes', db_index=True)
    uuid = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)
    
    TIPO_IDENTIFICACION_CHOICES = (
        ('RNC', 'RNC'),
        ('CEDULA', 'Cédula'),
        ('PASAPORTE', 'Pasaporte'),
        ('OTRO', 'Otro'),
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
    telefono = models.CharField(max_length=20, blank=True, null=True)
    correo_electronico = models.EmailField(blank=True, null=True)
    direccion = models.TextField(blank=True, null=True)
    limite_credito = models.DecimalField(
        max_digits=12, 
        decimal_places=2, 
        default=0,
        validators=[MinValueValidator(0)]
    )
    vendedor_asignado = models.ForeignKey(
        Vendedor, 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True,
        related_name='clientes',
        db_index=True,
        help_text="Vendedor asignado por defecto a este cliente"
    )
    activo = models.BooleanField(default=True, db_index=True)
    
    fecha_creacion = models.DateTimeField(auto_now_add=True)
    fecha_actualizacion = models.DateTimeField(auto_now=True)
    usuario_creacion = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name='clientes_creados', null=True, blank=True)
    usuario_modificacion = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name='clientes_modificados', null=True, blank=True)
    idempotency_key = models.CharField(max_length=100, unique=True, blank=True, null=True)

    class Meta:
        verbose_name = 'Cliente'
        verbose_name_plural = 'Clientes'
        ordering = ['nombre']
        unique_together = ('empresa', 'numero_identificacion')
        indexes = [
            models.Index(fields=['empresa', 'activo']),
            models.Index(fields=['empresa', 'tipo_identificacion', 'numero_identificacion']),
            models.Index(fields=['vendedor_asignado', 'activo']),
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
        
        # Validar que categoria pertenezca a la misma empresa
        if self.categoria and self.empresa and self.categoria.empresa != self.empresa:
            raise ValidationError({'categoria': 'La categoría debe pertenecer a la misma empresa del cliente.'})
        
        # Validar que vendedor pertenezca a la misma empresa
        if self.vendedor_asignado and self.empresa and self.vendedor_asignado.empresa != self.empresa:
            raise ValidationError({'vendedor_asignado': 'El vendedor debe pertenecer a la misma empresa del cliente.'})
        
        if self.limite_credito < 0:
            raise ValidationError({'limite_credito': 'El límite de crédito no puede ser negativo.'})
        
        if self.correo_electronico:
            self.correo_electronico = self.correo_electronico.strip().lower()

    @property
    def tipo_identificacion_display(self):
        """Obtener el display del tipo de identificación"""
        return self.get_tipo_identificacion_display() if self.tipo_identificacion else None

    def __str__(self):
        identificacion = f" ({self.numero_identificacion})" if self.numero_identificacion else ""
        return f"{self.nombre}{identificacion}"
