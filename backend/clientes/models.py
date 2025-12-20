"""
Modelos para el módulo de Clientes

Este módulo contiene los modelos Cliente y CategoriaCliente,
siguiendo los estándares de la Guía Inicial.
"""
from django.db import models
from django.conf import settings
from django.core.validators import MinValueValidator, MaxValueValidator
from django.core.exceptions import ValidationError
from vendedores.models import Vendedor
import uuid

from .constants import (
    TIPO_IDENTIFICACION_CHOICES,
    TIPO_IDENTIFICACION_RNC,
    TIPOS_REQUIEREN_NUMERO,
    DESCUENTO_MIN,
    DESCUENTO_MAX,
    LIMITE_CREDITO_MIN,
    ERROR_NOMBRE_VACIO,
    ERROR_DESCUENTO_RANGO,
    ERROR_LIMITE_CREDITO_NEGATIVO,
    ERROR_NUMERO_IDENTIFICACION_REQUERIDO,
    ERROR_CATEGORIA_OTRA_EMPRESA,
    ERROR_VENDEDOR_OTRA_EMPRESA,
    ERROR_CATEGORIA_DUPLICADA,
    ERROR_CLIENTE_IDENTIFICACION_DUPLICADA,
)

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
        """
        Validaciones de negocio para CategoriaCliente.

        CRÍTICO: Este método valida TODAS las reglas de negocio.
        """
        errors = {}

        # ========== VALIDACIONES DE VALORES ==========

        # Validar nombre no vacío
        if self.nombre:
            self.nombre = self.nombre.strip()
            if not self.nombre:
                errors['nombre'] = ERROR_NOMBRE_VACIO
        else:
            errors['nombre'] = ERROR_NOMBRE_VACIO

        # Validar rango de descuento
        if self.descuento_porcentaje is not None:
            if self.descuento_porcentaje < DESCUENTO_MIN or self.descuento_porcentaje > DESCUENTO_MAX:
                errors['descuento_porcentaje'] = ERROR_DESCUENTO_RANGO

        # ========== VALIDACIONES DE UNICIDAD ==========

        # Validar unicidad de nombre por empresa
        if self.nombre and self.empresa:
            qs = CategoriaCliente.objects.filter(
                nombre=self.nombre,
                empresa=self.empresa
            )
            if self.pk:
                qs = qs.exclude(pk=self.pk)
            if qs.exists():
                errors['nombre'] = ERROR_CATEGORIA_DUPLICADA

        if errors:
            raise ValidationError(errors)

    def save(self, *args, **kwargs):
        """
        Guarda el modelo con validaciones.

        CRÍTICO: Siempre ejecutar validaciones antes de guardar.
        """
        if 'update_fields' not in kwargs:
            self.full_clean()
        else:
            # Validar si se actualizan campos críticos
            update_fields = kwargs.get('update_fields', [])
            campos_criticos = ['empresa', 'descuento_porcentaje', 'nombre']
            if any(campo in update_fields for campo in campos_criticos):
                self.full_clean()

        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.nombre} ({self.empresa.nombre if self.empresa else 'Sin empresa'})"


class Cliente(models.Model):
    """
    Modelo para gestionar clientes de la empresa.

    Incluye campos de identificación, contacto, crédito y relaciones
    con categorías y vendedores.
    """
    empresa = models.ForeignKey(
        'empresas.Empresa',
        on_delete=models.PROTECT,
        related_name='clientes',
        null=True,
        blank=True,
        db_index=True,
        help_text='Empresa a la que pertenece el cliente'
    )
    categoria = models.ForeignKey(
        CategoriaCliente,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='clientes',
        db_index=True
    )
    uuid = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)

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
        """
        Validaciones de negocio para Cliente.

        CRÍTICO: Este método valida TODAS las reglas de negocio.
        """
        errors = {}

        # ========== VALIDACIONES DE VALORES ==========

        # Validar nombre no vacío
        if self.nombre:
            self.nombre = self.nombre.strip()
            if not self.nombre:
                errors['nombre'] = ERROR_NOMBRE_VACIO
        else:
            errors['nombre'] = ERROR_NOMBRE_VACIO

        # Validar límite de crédito no negativo
        if self.limite_credito is not None and self.limite_credito < LIMITE_CREDITO_MIN:
            errors['limite_credito'] = ERROR_LIMITE_CREDITO_NEGATIVO

        # ========== VALIDACIONES DE IDENTIFICACIÓN ==========

        # Validar que tipos específicos requieren número de identificación
        if self.tipo_identificacion in TIPOS_REQUIEREN_NUMERO:
            if not self.numero_identificacion:
                errors['numero_identificacion'] = ERROR_NUMERO_IDENTIFICACION_REQUERIDO.format(
                    tipo=self.tipo_identificacion
                )

        # ========== VALIDACIONES DE RELACIONES ==========

        # Validar que categoria pertenezca a la misma empresa
        if self.categoria and self.empresa:
            if self.categoria.empresa and self.categoria.empresa != self.empresa:
                errors['categoria'] = ERROR_CATEGORIA_OTRA_EMPRESA

        # Validar que vendedor pertenezca a la misma empresa
        if self.vendedor_asignado and self.empresa:
            if self.vendedor_asignado.empresa and self.vendedor_asignado.empresa != self.empresa:
                errors['vendedor_asignado'] = ERROR_VENDEDOR_OTRA_EMPRESA

        # ========== VALIDACIONES DE UNICIDAD ==========

        # Validar unicidad de numero_identificacion por empresa
        if self.numero_identificacion and self.empresa:
            qs = Cliente.objects.filter(
                numero_identificacion=self.numero_identificacion,
                empresa=self.empresa
            )
            if self.pk:
                qs = qs.exclude(pk=self.pk)
            if qs.exists():
                errors['numero_identificacion'] = ERROR_CLIENTE_IDENTIFICACION_DUPLICADA

        # ========== NORMALIZACIÓN DE DATOS ==========

        # Normalizar correo electrónico
        if self.correo_electronico:
            self.correo_electronico = self.correo_electronico.strip().lower()

        if errors:
            raise ValidationError(errors)

    def save(self, *args, **kwargs):
        """
        Guarda el modelo con validaciones.

        CRÍTICO: Siempre ejecutar validaciones antes de guardar.
        """
        if 'update_fields' not in kwargs:
            self.full_clean()
        else:
            # Validar si se actualizan campos críticos
            update_fields = kwargs.get('update_fields', [])
            campos_criticos = [
                'empresa', 'categoria', 'vendedor_asignado',
                'limite_credito', 'tipo_identificacion', 'numero_identificacion'
            ]
            if any(campo in update_fields for campo in campos_criticos):
                self.full_clean()

        super().save(*args, **kwargs)

    @property
    def tipo_identificacion_display(self):
        """Obtener el display del tipo de identificación"""
        return self.get_tipo_identificacion_display() if self.tipo_identificacion else None

    def __str__(self):
        identificacion = f" ({self.numero_identificacion})" if self.numero_identificacion else ""
        return f"{self.nombre}{identificacion}"
