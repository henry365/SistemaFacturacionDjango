"""
Modelos para el módulo de Despachos

Gestiona el despacho de productos desde almacenes hacia clientes,
vinculado a facturas de venta.
"""
from django.db import models
from django.conf import settings
from django.core.exceptions import ValidationError
from django.utils import timezone
import uuid

from .constants import (
    ESTADO_CHOICES, ESTADO_PENDIENTE, ESTADO_COMPLETADO, ESTADO_CANCELADO,
    ESTADOS_TERMINALES, TRANSICIONES_ESTADO,
    ERROR_FACTURA_EMPRESA, ERROR_CLIENTE_EMPRESA, ERROR_ALMACEN_EMPRESA,
    ERROR_CLIENTE_FACTURA, ERROR_FECHA_DESPACHO_FUTURA, ERROR_FECHA_DESPACHO_ANTERIOR,
    ERROR_TRANSICION_INVALIDA, ERROR_CANTIDAD_SOLICITADA_POSITIVA,
    ERROR_CANTIDAD_DESPACHADA_NEGATIVA, ERROR_CANTIDAD_EXCEDE_SOLICITADA,
    ERROR_PRODUCTO_EMPRESA
)


class Despacho(models.Model):
    """
    Representa un despacho de productos desde un almacén hacia un cliente.
    Se genera a partir de una Factura de venta.
    """
    empresa = models.ForeignKey(
        'empresas.Empresa',
        on_delete=models.PROTECT,
        related_name='despachos',
        db_index=True,
        null=True,
        blank=True
    )
    factura = models.ForeignKey(
        'ventas.Factura',
        on_delete=models.PROTECT,
        related_name='despachos',
        db_index=True
    )
    cliente = models.ForeignKey(
        'clientes.Cliente',
        on_delete=models.PROTECT,
        related_name='despachos',
        db_index=True
    )
    fecha = models.DateTimeField(auto_now_add=True)
    fecha_despacho = models.DateTimeField(
        null=True,
        blank=True,
        db_index=True,
        help_text="Fecha efectiva del despacho"
    )
    almacen = models.ForeignKey(
        'inventario.Almacen',
        on_delete=models.PROTECT,
        related_name='despachos',
        db_index=True
    )
    estado = models.CharField(
        max_length=20,
        choices=ESTADO_CHOICES,
        default=ESTADO_PENDIENTE,
        db_index=True
    )

    # Información de entrega
    direccion_entrega = models.TextField(blank=True, null=True)
    transportista = models.CharField(max_length=200, blank=True, null=True)
    numero_guia = models.CharField(max_length=100, blank=True, null=True, db_index=True)
    observaciones = models.TextField(blank=True, null=True)

    # Auditoría
    uuid = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)
    idempotency_key = models.CharField(max_length=100, unique=True, blank=True, null=True)
    fecha_creacion = models.DateTimeField(auto_now_add=True)
    fecha_actualizacion = models.DateTimeField(auto_now=True)
    usuario_creacion = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        related_name='despachos_creados',
        null=True,
        blank=True
    )
    usuario_modificacion = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        related_name='despachos_modificados',
        null=True,
        blank=True
    )
    usuario_despacho = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        related_name='despachos_realizados',
        null=True,
        blank=True
    )

    class Meta:
        verbose_name = 'Despacho'
        verbose_name_plural = 'Despachos'
        ordering = ['-fecha']
        indexes = [
            models.Index(fields=['empresa', 'estado']),
            models.Index(fields=['empresa', 'fecha_creacion']),
            models.Index(fields=['cliente', 'estado']),
        ]

    def clean(self):
        """Validaciones de negocio para Despacho"""
        errors = {}

        # Validar que la factura pertenece a la empresa
        if self.empresa and self.factura:
            if hasattr(self.factura, 'empresa') and self.factura.empresa:
                if self.factura.empresa != self.empresa:
                    errors['factura'] = ERROR_FACTURA_EMPRESA

        # Validar que el cliente pertenece a la empresa
        if self.empresa and self.cliente:
            if hasattr(self.cliente, 'empresa') and self.cliente.empresa:
                if self.cliente.empresa != self.empresa:
                    errors['cliente'] = ERROR_CLIENTE_EMPRESA

        # Validar que el almacén pertenece a la empresa
        if self.empresa and self.almacen:
            if hasattr(self.almacen, 'empresa') and self.almacen.empresa:
                if self.almacen.empresa != self.empresa:
                    errors['almacen'] = ERROR_ALMACEN_EMPRESA

        # Validar consistencia cliente-factura
        if self.factura and self.cliente:
            if hasattr(self.factura, 'cliente') and self.factura.cliente:
                if self.factura.cliente != self.cliente:
                    errors['cliente'] = ERROR_CLIENTE_FACTURA

        # Validar fecha de despacho
        if self.fecha_despacho:
            now = timezone.now()
            if self.fecha_despacho > now:
                errors['fecha_despacho'] = ERROR_FECHA_DESPACHO_FUTURA
            if self.fecha_creacion and self.fecha_despacho < self.fecha_creacion:
                errors['fecha_despacho'] = ERROR_FECHA_DESPACHO_ANTERIOR

        # Validar transiciones de estado
        if self.pk:
            try:
                estado_anterior = type(self).objects.get(pk=self.pk).estado
                if not self._es_transicion_valida(estado_anterior, self.estado):
                    errors['estado'] = ERROR_TRANSICION_INVALIDA.format(
                        estado_actual=estado_anterior,
                        estado_nuevo=self.estado
                    )
            except type(self).DoesNotExist:
                pass

        if errors:
            raise ValidationError(errors)

    def _es_transicion_valida(self, estado_actual, estado_nuevo):
        """Verifica si la transición de estado es válida"""
        if estado_actual == estado_nuevo:
            return True
        transiciones_permitidas = TRANSICIONES_ESTADO.get(estado_actual, [])
        return estado_nuevo in transiciones_permitidas

    def puede_cambiar_a_estado(self, nuevo_estado):
        """Verifica si se puede cambiar al nuevo estado"""
        return self._es_transicion_valida(self.estado, nuevo_estado)

    def save(self, *args, **kwargs):
        """Guarda con validaciones"""
        update_fields = kwargs.get('update_fields')
        campos_criticos = [
            'empresa', 'factura', 'cliente', 'almacen',
            'estado', 'fecha_despacho'
        ]

        if update_fields is None or any(f in update_fields for f in campos_criticos):
            self.full_clean()

        super().save(*args, **kwargs)

    def __str__(self):
        factura_num = self.factura.numero_factura if self.factura else 'N/A'
        return f"Despacho {self.id} - Factura {factura_num}"


class DetalleDespacho(models.Model):
    """
    Detalle de productos despachados.
    Registra las cantidades solicitadas vs despachadas.
    """
    despacho = models.ForeignKey(
        Despacho,
        on_delete=models.CASCADE,
        related_name='detalles',
        db_index=True
    )
    producto = models.ForeignKey(
        'productos.Producto',
        on_delete=models.PROTECT,
        db_index=True
    )
    cantidad_solicitada = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        help_text="Cantidad en factura"
    )
    cantidad_despachada = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=0,
        help_text="Cantidad efectivamente despachada"
    )
    lote = models.ForeignKey(
        'inventario.Lote',
        on_delete=models.SET_NULL,
        null=True,
        blank=True
    )
    observaciones = models.TextField(blank=True, null=True)

    # Mantener cantidad para compatibilidad
    cantidad = models.DecimalField(max_digits=12, decimal_places=2, default=0)

    # Auditoría
    uuid = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)
    fecha_creacion = models.DateTimeField(auto_now_add=True)
    fecha_actualizacion = models.DateTimeField(auto_now=True)
    usuario_creacion = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='detalles_despacho_creados'
    )
    usuario_modificacion = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='detalles_despacho_modificados'
    )

    class Meta:
        verbose_name = 'Detalle de Despacho'
        verbose_name_plural = 'Detalles de Despachos'
        unique_together = ('despacho', 'producto')
        indexes = [
            models.Index(fields=['despacho', 'producto']),
        ]

    def clean(self):
        """Validaciones de negocio para DetalleDespacho"""
        errors = {}

        # Validar cantidad solicitada
        if self.cantidad_solicitada is not None and self.cantidad_solicitada <= 0:
            errors['cantidad_solicitada'] = ERROR_CANTIDAD_SOLICITADA_POSITIVA

        # Validar cantidad despachada no negativa
        if self.cantidad_despachada is not None and self.cantidad_despachada < 0:
            errors['cantidad_despachada'] = ERROR_CANTIDAD_DESPACHADA_NEGATIVA

        # Validar que cantidad despachada no exceda solicitada
        if (self.cantidad_solicitada is not None and
            self.cantidad_despachada is not None and
            self.cantidad_despachada > self.cantidad_solicitada):
            errors['cantidad_despachada'] = ERROR_CANTIDAD_EXCEDE_SOLICITADA

        # Validar que el producto pertenece a la empresa del despacho
        if self.despacho and self.producto:
            if (self.despacho.empresa and
                hasattr(self.producto, 'empresa') and
                self.producto.empresa and
                self.despacho.empresa != self.producto.empresa):
                errors['producto'] = ERROR_PRODUCTO_EMPRESA

        if errors:
            raise ValidationError(errors)

    def save(self, *args, **kwargs):
        """Guarda con validaciones y sincroniza cantidad"""
        update_fields = kwargs.get('update_fields')
        campos_criticos = [
            'despacho', 'producto', 'cantidad_solicitada',
            'cantidad_despachada', 'lote'
        ]

        if update_fields is None or any(f in update_fields for f in campos_criticos):
            self.full_clean()

        # Mantener cantidad sincronizada con cantidad_despachada
        self.cantidad = self.cantidad_despachada

        super().save(*args, **kwargs)

    def __str__(self):
        producto_nombre = self.producto.nombre if self.producto else 'N/A'
        return f"{producto_nombre} - {self.cantidad_despachada}/{self.cantidad_solicitada}"
