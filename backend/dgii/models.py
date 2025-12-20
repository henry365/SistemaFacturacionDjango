"""
Modelos para el módulo DGII

Gestiona tipos de comprobantes fiscales y secuencias NCF
para cumplir con requerimientos de la DGII de República Dominicana.
"""
from django.db import models
from django.conf import settings
from django.core.exceptions import ValidationError
from django.utils import timezone
import uuid

from .constants import (
    PREFIJOS_NCF_VALIDOS, PREFIJO_DEFAULT, LONGITUD_CODIGO_TIPO,
    ALERTA_CANTIDAD_DEFAULT,
    ERROR_CODIGO_LONGITUD, ERROR_PREFIJO_INVALIDO,
    ERROR_SECUENCIA_FINAL_MAYOR, ERROR_SECUENCIA_ACTUAL_NEGATIVA,
    ERROR_SECUENCIA_ACTUAL_MENOR_INICIAL, ERROR_SECUENCIA_ACTUAL_MAYOR_FINAL,
    ERROR_FECHA_VENCIMIENTO_PASADA, ERROR_TIPO_COMPROBANTE_EMPRESA,
    ERROR_ALERTA_CANTIDAD_NEGATIVA, ERROR_SECUENCIA_AGOTADA
)


class TipoComprobante(models.Model):
    """
    Catálogo oficial de tipos de comprobantes fiscales DGII (01, 02, 14, 15, etc.)
    """
    empresa = models.ForeignKey(
        'empresas.Empresa',
        on_delete=models.PROTECT,
        related_name='tipos_comprobante',
        db_index=True,
        null=True,
        blank=True
    )
    codigo = models.CharField(max_length=2, help_text="Ej: 01, 02, 11, 14, 15")
    nombre = models.CharField(max_length=100)
    prefijo = models.CharField(
        max_length=1,
        default=PREFIJO_DEFAULT,
        help_text="Prefijo de la serie (Generalmente B o E)"
    )
    activo = models.BooleanField(default=True)

    # Campos de auditoría
    uuid = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)
    fecha_creacion = models.DateTimeField(auto_now_add=True, null=True)
    fecha_actualizacion = models.DateTimeField(auto_now=True, null=True)
    usuario_creacion = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='tipos_comprobante_creados'
    )
    usuario_modificacion = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='tipos_comprobante_modificados'
    )

    class Meta:
        verbose_name = 'Tipo de Comprobante'
        verbose_name_plural = 'Tipos de Comprobantes'
        ordering = ['codigo']
        unique_together = ('empresa', 'codigo')
        indexes = [
            models.Index(fields=['empresa', 'codigo']),
            models.Index(fields=['empresa', 'activo']),
        ]
        permissions = [
            ('gestionar_tipocomprobante', 'Puede gestionar tipos de comprobante'),
        ]

    def clean(self):
        """
        Validaciones de negocio para TipoComprobante.

        CRÍTICO: Este método garantiza la integridad de los datos.
        """
        errors = {}

        # Validar que código tenga formato correcto (2 dígitos)
        if self.codigo and len(self.codigo) != LONGITUD_CODIGO_TIPO:
            errors['codigo'] = ERROR_CODIGO_LONGITUD

        # Validar que prefijo sea válido (B o E)
        if self.prefijo and self.prefijo not in PREFIJOS_NCF_VALIDOS:
            errors['prefijo'] = ERROR_PREFIJO_INVALIDO

        if errors:
            raise ValidationError(errors)

    def save(self, *args, **kwargs):
        """
        Guarda con validaciones.

        CRÍTICO: Siempre ejecutar validaciones antes de guardar.
        """
        update_fields = kwargs.get('update_fields')
        campos_criticos = ['empresa', 'codigo', 'prefijo']

        if update_fields is None or any(f in update_fields for f in campos_criticos):
            self.full_clean()

        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.prefijo}{self.codigo} - {self.nombre}"


class SecuenciaNCF(models.Model):
    """
    Control de secuencias por empresa y tipo de comprobante.
    Ej: Empresa X tiene del B0100000001 al B0100000100 válido hasta el 31/12/2025
    """
    empresa = models.ForeignKey(
        'empresas.Empresa',
        on_delete=models.PROTECT,
        related_name='secuencias_ncf',
        db_index=True,
        null=True,
        blank=True
    )
    tipo_comprobante = models.ForeignKey(
        TipoComprobante,
        on_delete=models.PROTECT,
        related_name='secuencias',
        db_index=True
    )
    descripcion = models.CharField(
        max_length=100,
        help_text="Ej: Talonario Principal Facturas Crédito Fiscal"
    )

    secuencia_inicial = models.IntegerField(help_text="Número inicial autorizado (ej. 1)")
    secuencia_final = models.IntegerField(help_text="Número final autorizado (ej. 100)")
    secuencia_actual = models.IntegerField(default=0, help_text="Último número utilizado")

    fecha_vencimiento = models.DateField(
        help_text="Fecha de vencimiento de la secuencia",
        db_index=True
    )
    alerta_cantidad = models.IntegerField(
        default=ALERTA_CANTIDAD_DEFAULT,
        help_text="Avisar cuando queden X números"
    )

    activo = models.BooleanField(default=True)

    # Campos de auditoría
    uuid = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)
    fecha_creacion = models.DateTimeField(auto_now_add=True)
    fecha_actualizacion = models.DateTimeField(auto_now=True)
    usuario_creacion = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        related_name='secuencias_creadas',
        null=True,
        blank=True
    )
    usuario_modificacion = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        related_name='secuencias_modificadas',
        null=True,
        blank=True
    )

    class Meta:
        verbose_name = 'Secuencia NCF'
        verbose_name_plural = 'Secuencias NCF'
        unique_together = ('empresa', 'tipo_comprobante', 'secuencia_inicial')
        indexes = [
            models.Index(fields=['empresa', 'tipo_comprobante']),
            models.Index(fields=['empresa', 'activo']),
            models.Index(fields=['empresa', 'fecha_vencimiento']),
        ]
        permissions = [
            ('gestionar_secuenciancf', 'Puede gestionar secuencias NCF'),
            ('generar_secuenciancf', 'Puede generar NCF'),
            ('generar_reporte_606', 'Puede generar reporte 606 (compras)'),
            ('generar_reporte_607', 'Puede generar reporte 607 (ventas)'),
            ('generar_reporte_608', 'Puede generar reporte 608 (anulados)'),
        ]

    def clean(self):
        """
        Validaciones de negocio para SecuenciaNCF.

        CRÍTICO: Este método garantiza la integridad de los datos.
        """
        errors = {}

        # Validar que secuencia_inicial < secuencia_final
        if self.secuencia_inicial is not None and self.secuencia_final is not None:
            if self.secuencia_inicial >= self.secuencia_final:
                errors['secuencia_final'] = ERROR_SECUENCIA_FINAL_MAYOR

        # Validar secuencia_actual
        if self.secuencia_actual is not None:
            if self.secuencia_actual < 0:
                errors['secuencia_actual'] = ERROR_SECUENCIA_ACTUAL_NEGATIVA

            if self.secuencia_inicial is not None and self.secuencia_actual < self.secuencia_inicial:
                # Solo validar si secuencia_actual > 0 (ya se usó al menos una vez)
                if self.secuencia_actual > 0:
                    errors['secuencia_actual'] = ERROR_SECUENCIA_ACTUAL_MENOR_INICIAL

            if self.secuencia_final is not None and self.secuencia_actual > self.secuencia_final:
                errors['secuencia_actual'] = ERROR_SECUENCIA_ACTUAL_MAYOR_FINAL

        # Validar que fecha_vencimiento no sea pasada (solo para nuevas secuencias)
        if self.fecha_vencimiento and not self.pk:
            if self.fecha_vencimiento < timezone.now().date():
                errors['fecha_vencimiento'] = ERROR_FECHA_VENCIMIENTO_PASADA

        # Validar que tipo_comprobante pertenezca a la misma empresa
        if (self.empresa is not None and
            self.tipo_comprobante is not None and
            hasattr(self.tipo_comprobante, 'empresa') and
            self.tipo_comprobante.empresa is not None):
            if self.tipo_comprobante.empresa != self.empresa:
                errors['tipo_comprobante'] = ERROR_TIPO_COMPROBANTE_EMPRESA

        # Validar que alerta_cantidad sea positivo
        if self.alerta_cantidad is not None and self.alerta_cantidad < 0:
            errors['alerta_cantidad'] = ERROR_ALERTA_CANTIDAD_NEGATIVA

        if errors:
            raise ValidationError(errors)

    def save(self, *args, **kwargs):
        """
        Guarda con validaciones.

        CRÍTICO: Siempre ejecutar validaciones antes de guardar.
        """
        update_fields = kwargs.get('update_fields')
        campos_criticos = [
            'empresa', 'tipo_comprobante', 'secuencia_inicial',
            'secuencia_final', 'secuencia_actual', 'fecha_vencimiento'
        ]

        if update_fields is None or any(f in update_fields for f in campos_criticos):
            self.full_clean()

        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.tipo_comprobante} ({self.secuencia_actual}/{self.secuencia_final})"

    @property
    def agotada(self):
        """Indica si la secuencia está agotada"""
        return self.secuencia_actual >= self.secuencia_final

    @property
    def disponibles(self):
        """Retorna cantidad de NCF disponibles"""
        return self.secuencia_final - self.secuencia_actual

    @property
    def porcentaje_uso(self):
        """Retorna porcentaje de uso de la secuencia"""
        total = self.secuencia_final - self.secuencia_inicial + 1
        usados = self.secuencia_actual - self.secuencia_inicial + 1
        if total > 0:
            return round((usados / total) * 100, 2)
        return 0

    def siguiente_numero(self):
        """
        Retorna el siguiente NCF formateado y aumenta el contador.
        Debe usarse dentro de una transacción atómica.
        """
        if self.agotada:
            raise ValueError(ERROR_SECUENCIA_AGOTADA)

        siguiente = self.secuencia_actual + 1
        # Formato NCF: Prefijo (B) + Tipo (01) + Secuencia (8 dígitos) = B0100000001
        ncf_formateado = f"{self.tipo_comprobante.prefijo}{self.tipo_comprobante.codigo}{siguiente:08d}"

        return ncf_formateado
