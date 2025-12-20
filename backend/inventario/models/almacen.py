"""
Modelos de almacén e inventario de productos.
"""
from django.db import models
from django.conf import settings
from django.core.exceptions import ValidationError
from django.utils import timezone
from django.db.models import Sum, F, GeneratedField, OuterRef, Subquery, Value
from django.db.models.functions import Coalesce
from productos.models import Producto
from datetime import timedelta
import uuid

from ..constants import (
    ERROR_NOMBRE_VACIO, ERROR_NOMBRE_REQUERIDO, ERROR_NOMBRE_DUPLICADO_EMPRESA,
    ERROR_CANTIDAD_NEGATIVA, ERROR_COSTO_NEGATIVO,
    ERROR_STOCK_MINIMO_MAYOR_MAXIMO, ERROR_PUNTO_REORDEN_MENOR_MINIMO,
    ERROR_PUNTO_REORDEN_MAYOR_MAXIMO,
    ERROR_PRODUCTO_NO_PERTENECE_EMPRESA, ERROR_ALMACEN_NO_PERTENECE_EMPRESA,
)


class InventarioProductoQuerySet(models.QuerySet):
    """
    QuerySet personalizado para InventarioProducto.

    Django 6.0: Usa Subquery para evitar N+1 en stock_reservado.
    """

    def with_stock_reservado(self):
        """Anota el queryset con stock_reservado calculado mediante Subquery."""
        from .movimientos import ReservaStock

        reservas_subquery = ReservaStock.objects.filter(
            inventario=OuterRef('pk'),
            estado__in=['PENDIENTE', 'CONFIRMADA']
        ).values('inventario').annotate(
            total=Sum('cantidad_reservada')
        ).values('total')

        return self.annotate(
            stock_reservado_anotado=Coalesce(
                Subquery(reservas_subquery),
                Value(0),
                output_field=models.DecimalField(max_digits=12, decimal_places=2)
            )
        )

    def with_stock_disponible_real(self):
        """Anota el queryset con stock disponible real (cantidad - reservado)."""
        return self.with_stock_reservado().annotate(
            stock_disponible_real_anotado=F('cantidad_disponible') - F('stock_reservado_anotado')
        )

    def with_rotacion(self, dias=30):
        """Anota el queryset con la rotación de inventario usando Subquery."""
        from django.apps import apps

        fecha_limite = timezone.now() - timedelta(days=dias)

        MovimientoInventario = apps.get_model('inventario', 'MovimientoInventario')

        salidas_subquery = MovimientoInventario.objects.filter(
            producto=OuterRef('producto'),
            almacen=OuterRef('almacen'),
            tipo_movimiento__in=['SALIDA_VENTA', 'TRANSFERENCIA_SALIDA'],
            fecha__gte=fecha_limite
        ).values('producto', 'almacen').annotate(
            total=Sum('cantidad')
        ).values('total')

        return self.annotate(
            salidas_periodo=Coalesce(
                Subquery(salidas_subquery),
                Value(0),
                output_field=models.DecimalField(max_digits=12, decimal_places=2)
            )
        )


class InventarioProductoManager(models.Manager):
    """Manager personalizado que usa InventarioProductoQuerySet."""

    def get_queryset(self):
        return InventarioProductoQuerySet(self.model, using=self._db)

    def with_stock_reservado(self):
        return self.get_queryset().with_stock_reservado()

    def with_stock_disponible_real(self):
        return self.get_queryset().with_stock_disponible_real()

    def with_rotacion(self, dias=30):
        return self.get_queryset().with_rotacion(dias=dias)


class Almacen(models.Model):
    """Almacén físico para almacenar inventario."""

    empresa = models.ForeignKey(
        'empresas.Empresa',
        on_delete=models.PROTECT,
        related_name='almacenes',
        null=True,
        blank=True
    )
    nombre = models.CharField(max_length=100)
    descripcion = models.TextField(blank=True, null=True)
    direccion = models.TextField(blank=True, null=True)
    activo = models.BooleanField(default=True)

    # Campos de auditoría
    uuid = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)
    idempotency_key = models.CharField(max_length=100, unique=True, blank=True, null=True)
    fecha_creacion = models.DateTimeField(auto_now_add=True)
    fecha_actualizacion = models.DateTimeField(auto_now=True, null=True)
    usuario_creacion = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name='almacenes_creados',
        null=True,
        blank=True
    )
    usuario_modificacion = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name='almacenes_modificados',
        null=True,
        blank=True
    )

    class Meta:
        verbose_name = 'Almacén'
        verbose_name_plural = 'Almacenes'
        unique_together = ('empresa', 'nombre')
        indexes = [
            models.Index(fields=['empresa', 'activo']),
            models.Index(fields=['empresa', 'nombre']),
        ]
        permissions = [
            ('gestionar_almacen', 'Puede gestionar almacenes'),
        ]

    def clean(self):
        """Validaciones de negocio para Almacen."""
        errors = {}

        # Validar nombre no vacío
        if self.nombre:
            self.nombre = self.nombre.strip()
            if not self.nombre:
                errors['nombre'] = ERROR_NOMBRE_VACIO
        else:
            errors['nombre'] = ERROR_NOMBRE_REQUERIDO

        # Validar unicidad de nombre por empresa
        if self.nombre and self.empresa:
            qs = type(self).objects.filter(empresa=self.empresa, nombre=self.nombre)
            if self.pk:
                qs = qs.exclude(pk=self.pk)
            if qs.exists():
                errors['nombre'] = ERROR_NOMBRE_DUPLICADO_EMPRESA

        if errors:
            raise ValidationError(errors)

    def save(self, *args, **kwargs):
        """Guarda con validaciones."""
        update_fields = kwargs.get('update_fields')
        campos_criticos = ['nombre', 'empresa', 'activo']

        if update_fields is None or any(f in update_fields for f in campos_criticos):
            self.full_clean()

        super().save(*args, **kwargs)

    def __str__(self):
        return self.nombre


class InventarioProducto(models.Model):
    """Inventario de un producto en un almacén específico."""

    METODO_VALORACION_CHOICES = (
        ('PROMEDIO', 'Costo Promedio Ponderado'),
        ('PEPS', 'Primero en Entrar, Primero en Salir (FIFO)'),
        ('UEPS', 'Último en Entrar, Primero en Salir (LIFO)'),
        ('PRECIO_ESPECIFICO', 'Precio Específico'),
    )

    empresa = models.ForeignKey(
        'empresas.Empresa',
        on_delete=models.PROTECT,
        related_name='inventarios_productos',
        null=True,
        blank=True
    )
    producto = models.ForeignKey(Producto, on_delete=models.PROTECT, related_name='inventarios')
    almacen = models.ForeignKey(Almacen, on_delete=models.PROTECT, related_name='inventarios')
    cantidad_disponible = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    costo_promedio = models.DecimalField(max_digits=12, decimal_places=4, default=0)

    metodo_valoracion = models.CharField(
        max_length=20,
        choices=METODO_VALORACION_CHOICES,
        default='PROMEDIO',
        help_text="Método de valoración de inventario"
    )
    costo_unitario_actual = models.DecimalField(
        max_digits=12,
        decimal_places=4,
        default=0,
        help_text="Costo unitario actual según método de valoración"
    )

    # Django 6.0: Valor de inventario calculado automáticamente
    valor_inventario = GeneratedField(
        expression=F('cantidad_disponible') * F('costo_promedio'),
        output_field=models.DecimalField(max_digits=18, decimal_places=2),
        db_persist=True,
        help_text="Valor total del inventario (calculado automáticamente)"
    )

    # Control de stock
    stock_minimo = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    stock_maximo = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    punto_reorden = models.DecimalField(max_digits=12, decimal_places=2, default=0)

    # Campos de auditoría
    uuid = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)
    fecha_creacion = models.DateTimeField(auto_now_add=True)
    fecha_actualizacion = models.DateTimeField(auto_now=True, null=True)
    usuario_creacion = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name='inventarios_productos_creados',
        null=True,
        blank=True
    )
    usuario_modificacion = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name='inventarios_productos_modificados',
        null=True,
        blank=True
    )

    objects = InventarioProductoManager()

    class Meta:
        verbose_name = 'Inventario de Producto'
        verbose_name_plural = 'Inventarios de Productos'
        unique_together = ('producto', 'almacen')
        indexes = [
            models.Index(fields=['producto', 'almacen']),
            models.Index(fields=['cantidad_disponible']),
            models.Index(fields=['empresa', 'almacen']),
        ]
        permissions = [
            ('gestionar_inventarioproducto', 'Puede gestionar inventario'),
        ]

    def clean(self):
        """Validaciones de negocio para InventarioProducto."""
        errors = {}

        # Validar que producto y almacen pertenezcan a la empresa
        if self.producto and self.almacen and self.empresa:
            if hasattr(self.producto, 'empresa') and self.producto.empresa and self.producto.empresa != self.empresa:
                errors['producto'] = ERROR_PRODUCTO_NO_PERTENECE_EMPRESA

            if self.almacen.empresa and self.almacen.empresa != self.empresa:
                errors['almacen'] = ERROR_ALMACEN_NO_PERTENECE_EMPRESA

        # Validar que cantidad_disponible no sea negativa
        if self.cantidad_disponible < 0:
            errors['cantidad_disponible'] = ERROR_CANTIDAD_NEGATIVA

        # Validar stock_minimo <= stock_maximo
        if self.stock_minimo > 0 and self.stock_maximo > 0:
            if self.stock_minimo > self.stock_maximo:
                errors['stock_minimo'] = ERROR_STOCK_MINIMO_MAYOR_MAXIMO

        # Validar punto_reorden
        if self.punto_reorden > 0:
            if self.stock_minimo > 0 and self.punto_reorden < self.stock_minimo:
                errors['punto_reorden'] = ERROR_PUNTO_REORDEN_MENOR_MINIMO
            if self.stock_maximo > 0 and self.punto_reorden > self.stock_maximo:
                errors['punto_reorden'] = ERROR_PUNTO_REORDEN_MAYOR_MAXIMO

        # Validar costos no negativos
        if self.costo_promedio < 0:
            errors['costo_promedio'] = ERROR_COSTO_NEGATIVO
        if self.costo_unitario_actual < 0:
            errors['costo_unitario_actual'] = ERROR_COSTO_NEGATIVO

        if errors:
            raise ValidationError(errors)

    def save(self, *args, **kwargs):
        """Guarda con validaciones."""
        update_fields = kwargs.get('update_fields')
        campos_criticos = [
            'empresa', 'producto', 'almacen', 'cantidad_disponible',
            'stock_minimo', 'stock_maximo', 'punto_reorden',
            'costo_promedio', 'costo_unitario_actual'
        ]

        if update_fields is None or any(f in update_fields for f in campos_criticos):
            self.full_clean()

        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.producto} en {self.almacen}: {self.cantidad_disponible}"

    @property
    def esta_bajo_minimo(self):
        return self.cantidad_disponible <= self.stock_minimo

    @property
    def necesita_reorden(self):
        return self.cantidad_disponible <= self.punto_reorden

    @property
    def stock_reservado(self):
        from .movimientos import ReservaStock
        return ReservaStock.objects.filter(
            inventario=self,
            estado__in=['PENDIENTE', 'CONFIRMADA']
        ).aggregate(
            total=Sum('cantidad_reservada')
        )['total'] or 0

    @property
    def stock_disponible_real(self):
        return self.cantidad_disponible - self.stock_reservado

    def tiene_stock_suficiente(self, cantidad):
        return self.stock_disponible_real >= cantidad

    def actualizar_costo_promedio(self, nueva_cantidad, nuevo_costo):
        """Actualiza el costo promedio usando método de promedio ponderado."""
        from decimal import Decimal, ROUND_HALF_UP
        if self.cantidad_disponible == 0:
            self.costo_promedio = nuevo_costo
            self.costo_unitario_actual = nuevo_costo
        else:
            total_valor_actual = self.cantidad_disponible * self.costo_promedio
            total_valor_nuevo = nueva_cantidad * nuevo_costo
            cantidad_total = self.cantidad_disponible + nueva_cantidad
            # Redondear a 4 decimales para evitar exceder max_digits
            nuevo_promedio = (total_valor_actual + total_valor_nuevo) / cantidad_total
            self.costo_promedio = nuevo_promedio.quantize(Decimal('0.0001'), rounding=ROUND_HALF_UP)
            self.costo_unitario_actual = self.costo_promedio
        self.save()

    def rotacion_promedio(self, dias=30):
        """Calcula rotación de inventario en los últimos N días."""
        from .movimientos import MovimientoInventario

        fecha_limite = timezone.now() - timedelta(days=dias)
        salidas = MovimientoInventario.objects.filter(
            producto=self.producto,
            almacen=self.almacen,
            tipo_movimiento__in=['SALIDA_VENTA', 'TRANSFERENCIA_SALIDA'],
            fecha__gte=fecha_limite
        ).aggregate(total=Sum('cantidad'))['total'] or 0

        promedio_inventario = self.cantidad_disponible
        if promedio_inventario > 0:
            return salidas / promedio_inventario
        return 0

    def dias_inventario(self):
        """Días de inventario disponibles basado en rotación."""
        rotacion = self.rotacion_promedio(30)
        if rotacion > 0:
            return 30 / rotacion
        return None
