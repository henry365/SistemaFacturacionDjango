"""
Modelos para el módulo Productos

Este módulo contiene los modelos para gestión de productos, categorías,
imágenes y referencias cruzadas.

MULTI-TENANCY: Todos los modelos tienen campo `empresa` para aislamiento de datos.
"""
from django.db import models
from django.conf import settings
from django.core.validators import MinValueValidator
from django.core.exceptions import ValidationError
import uuid
import os
import re

from .constants import (
    TIPO_PRODUCTO_CHOICES,
    TIPO_REFERENCIA_CHOICES,
    TIPOS_PRODUCTO_SIN_STOCK,
    ITBIS_DEFAULT,
    SKU_REGEX,
    ERROR_NOMBRE_VACIO,
    ERROR_SKU_VACIO,
    ERROR_SKU_FORMATO,
    ERROR_SKU_DUPLICADO,
    ERROR_PRECIO_NEGATIVO,
    ERROR_ITBIS_RANGO,
    ERROR_DESCUENTO_PROMOCIONAL_RANGO,
    ERROR_DESCUENTO_MAXIMO_RANGO,
    ERROR_DESCUENTO_MAXIMO_MENOR,
    ERROR_MESES_GARANTIA_NEGATIVO,
    ERROR_MESES_GARANTIA_REQUERIDO,
    ERROR_PRODUCTO_ORIGEN_DESTINO_IGUAL,
    ERROR_NOMBRE_DUPLICADO,
)


class Categoria(models.Model):
    """
    Categorías para clasificar productos.

    Permite organizar productos en grupos lógicos.
    Cada empresa tiene sus propias categorías (multi-tenant).
    """
    empresa = models.ForeignKey(
        'empresas.Empresa',
        on_delete=models.CASCADE,
        related_name='categorias_producto',
        db_index=True,
        null=True,  # Temporarily nullable for migration
        blank=True,
        help_text="Empresa propietaria de la categoría"
    )
    nombre = models.CharField(max_length=100)
    descripcion = models.TextField(blank=True, null=True)
    activa = models.BooleanField(default=True, db_index=True)
    idempotency_key = models.CharField(max_length=100, unique=True, blank=True, null=True)

    # Campos de auditoría
    uuid = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)
    fecha_creacion = models.DateTimeField(auto_now_add=True)
    fecha_actualizacion = models.DateTimeField(auto_now=True)
    usuario_creacion = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='categorias_creadas'
    )
    usuario_modificacion = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='categorias_modificadas'
    )

    class Meta:
        verbose_name = 'Categoría'
        verbose_name_plural = 'Categorías'
        ordering = ['nombre']
        unique_together = [('empresa', 'nombre')]
        indexes = [
            models.Index(fields=['empresa', 'activa', 'nombre']),
        ]
        permissions = [
            ('gestionar_categoria', 'Puede gestionar categorías'),
        ]

    def clean(self):
        """
        Validaciones de negocio para Categoria.

        CRÍTICO: Este método garantiza la integridad de los datos.
        """
        errors = {}

        # Validar y normalizar nombre
        if self.nombre:
            self.nombre = self.nombre.strip()
            if not self.nombre:
                errors['nombre'] = ERROR_NOMBRE_VACIO
        else:
            errors['nombre'] = ERROR_NOMBRE_VACIO

        # Validar unicidad de nombre dentro de la empresa
        if self.nombre and self.empresa_id and not errors.get('nombre'):
            qs = Categoria.objects.filter(empresa=self.empresa, nombre=self.nombre)
            if self.pk:
                qs = qs.exclude(pk=self.pk)
            if qs.exists():
                errors['nombre'] = ERROR_NOMBRE_DUPLICADO

        if errors:
            raise ValidationError(errors)

    def save(self, *args, **kwargs):
        """
        Guarda con validaciones.

        CRÍTICO: Siempre ejecutar validaciones antes de guardar.
        """
        update_fields = kwargs.get('update_fields')
        campos_criticos = ['nombre', 'activa', 'empresa']

        if update_fields is None or any(f in update_fields for f in campos_criticos):
            self.full_clean()

        super().save(*args, **kwargs)

    def __str__(self):
        return self.nombre


class Producto(models.Model):
    """
    Modelo principal de productos.

    Define productos con precios, impuestos, descuentos y categorías.
    Cada empresa tiene su propio catálogo de productos (multi-tenant).
    """
    empresa = models.ForeignKey(
        'empresas.Empresa',
        on_delete=models.CASCADE,
        related_name='productos',
        db_index=True,
        null=True,  # Temporarily nullable for migration
        blank=True,
        help_text="Empresa propietaria del producto"
    )
    codigo_sku = models.CharField(max_length=50, db_index=True)
    nombre = models.CharField(max_length=200)
    descripcion = models.TextField(blank=True, null=True)

    tipo_producto = models.CharField(
        max_length=20,
        choices=TIPO_PRODUCTO_CHOICES,
        default='ALMACENABLE',
        db_index=True,
        help_text="Define cómo se comporta el producto en compras e inventario"
    )
    controlar_stock = models.BooleanField(
        default=True,
        help_text="Si es Falso, el sistema no validará existencias (útil para servicios o consumibles directos)"
    )

    precio_venta_base = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        validators=[MinValueValidator(0)]
    )
    impuesto_itbis = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        default=ITBIS_DEFAULT,
        validators=[MinValueValidator(0)],
        help_text="Porcentaje de ITBIS (ej. 18.00). Si es exento, colocar 0.00"
    )
    es_exento = models.BooleanField(
        default=False,
        db_index=True,
        help_text="Marcar si el producto está legalmente exonerado de ITBIS (ej. Transporte, Libros)"
    )

    tiene_garantia = models.BooleanField(default=False, help_text="Indica si el producto tiene garantía")
    meses_garantia = models.IntegerField(default=0, validators=[MinValueValidator(0)], help_text="Duración de la garantía en meses")

    # Campos de Descuento
    porcentaje_descuento_promocional = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        default=0.00,
        validators=[MinValueValidator(0)],
        help_text="Descuento automático aplicado al precio base"
    )
    porcentaje_descuento_maximo = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        default=0.00,
        validators=[MinValueValidator(0)],
        help_text="Máximo descuento manual permitido a vendedores"
    )

    categorias = models.ManyToManyField(Categoria, related_name='productos', blank=True)
    activo = models.BooleanField(default=True, db_index=True)
    idempotency_key = models.CharField(max_length=100, unique=True, blank=True, null=True)

    # Campos de auditoría
    uuid = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)
    fecha_creacion = models.DateTimeField(auto_now_add=True)
    fecha_actualizacion = models.DateTimeField(auto_now=True)
    usuario_creacion = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='productos_creados'
    )
    usuario_modificacion = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='productos_modificados'
    )

    class Meta:
        verbose_name = 'Producto'
        verbose_name_plural = 'Productos'
        ordering = ['nombre']
        unique_together = [('empresa', 'codigo_sku')]
        indexes = [
            models.Index(fields=['empresa', 'activo', 'tipo_producto']),
            models.Index(fields=['empresa', 'codigo_sku']),
            models.Index(fields=['empresa', '-fecha_creacion']),
        ]
        permissions = [
            ('gestionar_producto', 'Puede gestionar productos'),
            ('cargar_catalogo', 'Puede cargar catálogo masivo'),
        ]

    def clean(self):
        """
        Validaciones de negocio para Producto.

        CRÍTICO: Este método garantiza la integridad de los datos.
        """
        errors = {}

        # Validar y normalizar nombre
        if self.nombre:
            self.nombre = self.nombre.strip()
            if not self.nombre:
                errors['nombre'] = ERROR_NOMBRE_VACIO

        # Validar y normalizar SKU
        if self.codigo_sku:
            self.codigo_sku = self.codigo_sku.strip()
            if not self.codigo_sku:
                errors['codigo_sku'] = ERROR_SKU_VACIO
            elif not re.match(SKU_REGEX, self.codigo_sku):
                errors['codigo_sku'] = ERROR_SKU_FORMATO

        # Validar unicidad de codigo_sku dentro de la empresa
        if self.codigo_sku and self.empresa_id and not errors.get('codigo_sku'):
            qs = Producto.objects.filter(empresa=self.empresa, codigo_sku=self.codigo_sku)
            if self.pk:
                qs = qs.exclude(pk=self.pk)
            if qs.exists():
                errors['codigo_sku'] = ERROR_SKU_DUPLICADO

        # Validar precio
        if self.precio_venta_base is not None and self.precio_venta_base < 0:
            errors['precio_venta_base'] = ERROR_PRECIO_NEGATIVO

        # Validar ITBIS
        if self.impuesto_itbis is not None:
            if self.impuesto_itbis < 0 or self.impuesto_itbis > 100:
                errors['impuesto_itbis'] = ERROR_ITBIS_RANGO

        # Validar descuentos
        if self.porcentaje_descuento_promocional is not None:
            if self.porcentaje_descuento_promocional < 0 or self.porcentaje_descuento_promocional > 100:
                errors['porcentaje_descuento_promocional'] = ERROR_DESCUENTO_PROMOCIONAL_RANGO

        if self.porcentaje_descuento_maximo is not None:
            if self.porcentaje_descuento_maximo < 0 or self.porcentaje_descuento_maximo > 100:
                errors['porcentaje_descuento_maximo'] = ERROR_DESCUENTO_MAXIMO_RANGO

        # Validar que descuento máximo >= descuento promocional
        if (self.porcentaje_descuento_maximo is not None and
            self.porcentaje_descuento_promocional is not None and
            self.porcentaje_descuento_maximo < self.porcentaje_descuento_promocional):
            errors['porcentaje_descuento_maximo'] = ERROR_DESCUENTO_MAXIMO_MENOR

        # Validar meses de garantía
        if self.meses_garantia is not None and self.meses_garantia < 0:
            errors['meses_garantia'] = ERROR_MESES_GARANTIA_NEGATIVO

        # Validar que meses_garantia > 0 si tiene_garantia es True
        if self.tiene_garantia and (self.meses_garantia is None or self.meses_garantia <= 0):
            errors['meses_garantia'] = ERROR_MESES_GARANTIA_REQUERIDO

        if errors:
            raise ValidationError(errors)

        # Auto-configurar control de stock basado en tipo
        if self.tipo_producto in TIPOS_PRODUCTO_SIN_STOCK:
            self.controlar_stock = False

        # Si es exento, forzar ITBIS a 0
        if self.es_exento:
            self.impuesto_itbis = 0.00

        # Si no tiene garantía, asegurar que meses sea 0
        if not self.tiene_garantia:
            self.meses_garantia = 0

    def save(self, *args, **kwargs):
        """
        Guarda con validaciones.

        CRÍTICO: Siempre ejecutar validaciones antes de guardar.
        """
        update_fields = kwargs.get('update_fields')
        campos_criticos = [
            'nombre', 'codigo_sku', 'precio_venta_base', 'impuesto_itbis',
            'porcentaje_descuento_promocional', 'porcentaje_descuento_maximo',
            'tipo_producto', 'controlar_stock', 'es_exento', 'activo',
            'tiene_garantia', 'meses_garantia', 'empresa'
        ]

        if update_fields is None or any(f in update_fields for f in campos_criticos):
            self.full_clean()

        super().save(*args, **kwargs)

    @property
    def tipo_producto_display(self):
        """Obtener el display del tipo de producto"""
        return self.get_tipo_producto_display()

    def __str__(self):
        return f"{self.codigo_sku} - {self.nombre}"


def producto_imagen_path(instance, filename):
    """Genera la ruta de almacenamiento para imágenes de productos"""
    ext = filename.split('.')[-1]
    filename = f"{uuid.uuid4().hex}.{ext}"
    return os.path.join('productos', str(instance.producto_id), filename)


class ImagenProducto(models.Model):
    """
    Galería de imágenes para productos.

    Permite múltiples imágenes por producto con orden personalizable.
    La empresa se hereda del producto.
    """
    empresa = models.ForeignKey(
        'empresas.Empresa',
        on_delete=models.CASCADE,
        related_name='imagenes_producto',
        db_index=True,
        null=True,  # Temporarily nullable for migration
        blank=True,
        help_text="Empresa propietaria de la imagen"
    )
    producto = models.ForeignKey(
        Producto,
        on_delete=models.CASCADE,
        related_name='imagenes',
        db_index=True
    )
    imagen = models.ImageField(
        upload_to=producto_imagen_path,
        help_text="Imagen del producto (JPG, PNG, WebP recomendado)"
    )
    titulo = models.CharField(
        max_length=100,
        blank=True,
        null=True,
        help_text="Título o nombre descriptivo de la imagen"
    )
    descripcion = models.TextField(
        blank=True,
        null=True,
        help_text="Descripción alternativa (alt text) para accesibilidad"
    )
    es_principal = models.BooleanField(
        default=False,
        db_index=True,
        help_text="Marcar como imagen principal del producto"
    )
    orden = models.PositiveIntegerField(
        default=0,
        help_text="Orden de visualización (menor = primero)"
    )
    activa = models.BooleanField(
        default=True,
        db_index=True,
        help_text="Si está activa se muestra en el catálogo"
    )

    # Campos de auditoría
    uuid = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)
    fecha_creacion = models.DateTimeField(auto_now_add=True)
    fecha_actualizacion = models.DateTimeField(auto_now=True)
    usuario_creacion = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='imagenes_producto_creadas'
    )
    usuario_modificacion = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='imagenes_producto_modificadas'
    )

    class Meta:
        verbose_name = 'Imagen de Producto'
        verbose_name_plural = 'Imágenes de Productos'
        ordering = ['producto', 'orden', '-es_principal']
        indexes = [
            models.Index(fields=['empresa', 'producto', 'es_principal']),
            models.Index(fields=['empresa', 'producto', 'activa', 'orden']),
        ]
        permissions = [
            ('gestionar_imagenproducto', 'Puede gestionar imágenes de productos'),
        ]

    def clean(self):
        """
        Validaciones de negocio para ImagenProducto.
        """
        errors = {}

        # Validar que el producto pertenezca a la misma empresa
        if self.producto_id and self.empresa_id:
            if self.producto.empresa_id != self.empresa_id:
                errors['producto'] = 'El producto debe pertenecer a la misma empresa.'

        if errors:
            raise ValidationError(errors)

        # Si se marca como principal, desmarcar otras del mismo producto
        if self.es_principal and self.pk:
            ImagenProducto.objects.filter(
                producto=self.producto,
                es_principal=True
            ).exclude(pk=self.pk).update(es_principal=False)

    def save(self, *args, **kwargs):
        """
        Guarda con validaciones.

        CRÍTICO: Siempre ejecutar validaciones antes de guardar.
        """
        # Heredar empresa del producto si no está establecida
        if self.producto_id and not self.empresa_id:
            self.empresa_id = self.producto.empresa_id

        # Si es la primera imagen y no hay principal, marcarla como principal
        if not self.pk:
            existing = ImagenProducto.objects.filter(producto=self.producto)
            if not existing.exists():
                self.es_principal = True
            elif self.es_principal:
                # Desmarcar otras como principal
                existing.filter(es_principal=True).update(es_principal=False)

        update_fields = kwargs.get('update_fields')
        campos_criticos = ['producto', 'es_principal', 'orden', 'activa', 'empresa']

        if update_fields is None or any(f in update_fields for f in campos_criticos):
            self.full_clean()

        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.producto.codigo_sku} - Imagen {self.orden}"

    @property
    def url(self):
        """Retorna la URL de la imagen si existe"""
        if self.imagen:
            return self.imagen.url
        return None


class ReferenciasCruzadas(models.Model):
    """
    Referencias cruzadas entre productos.

    Define relaciones como productos relacionados, sustitutos, complementarios.
    Ambos productos deben pertenecer a la misma empresa.
    """
    empresa = models.ForeignKey(
        'empresas.Empresa',
        on_delete=models.CASCADE,
        related_name='referencias_producto',
        db_index=True,
        null=True,  # Temporarily nullable for migration
        blank=True,
        help_text="Empresa propietaria de la referencia"
    )
    producto_origen = models.ForeignKey(
        Producto,
        on_delete=models.CASCADE,
        related_name='referencias_desde',
        db_index=True
    )
    producto_destino = models.ForeignKey(
        Producto,
        on_delete=models.CASCADE,
        related_name='referencias_hacia',
        db_index=True
    )
    tipo = models.CharField(
        max_length=20,
        choices=TIPO_REFERENCIA_CHOICES,
        default='RELACIONADO',
        db_index=True
    )
    bidireccional = models.BooleanField(
        default=True,
        help_text="Si es True, la relación aplica en ambas direcciones"
    )
    activa = models.BooleanField(default=True, db_index=True)

    # Campos de auditoría
    uuid = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)
    fecha_creacion = models.DateTimeField(auto_now_add=True)
    fecha_actualizacion = models.DateTimeField(auto_now=True)
    usuario_creacion = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='referencias_creadas'
    )
    usuario_modificacion = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='referencias_modificadas'
    )

    class Meta:
        verbose_name = 'Referencia Cruzada'
        verbose_name_plural = 'Referencias Cruzadas'
        unique_together = [('empresa', 'producto_origen', 'producto_destino', 'tipo')]
        ordering = ['producto_origen', 'tipo']
        indexes = [
            models.Index(fields=['empresa', 'producto_origen', 'tipo', 'activa']),
            models.Index(fields=['empresa', 'producto_destino', 'bidireccional', 'activa']),
        ]
        permissions = [
            ('gestionar_referenciascruzadas', 'Puede gestionar referencias cruzadas'),
        ]

    def clean(self):
        """
        Validaciones de negocio para ReferenciasCruzadas.

        CRÍTICO: Este método garantiza la integridad de los datos.
        """
        errors = {}

        if self.producto_origen == self.producto_destino:
            errors['producto_destino'] = ERROR_PRODUCTO_ORIGEN_DESTINO_IGUAL

        # Validar que ambos productos pertenezcan a la misma empresa
        if self.producto_origen_id and self.producto_destino_id:
            if self.producto_origen.empresa_id != self.producto_destino.empresa_id:
                errors['producto_destino'] = 'Ambos productos deben pertenecer a la misma empresa.'

        # Validar que la referencia pertenezca a la misma empresa que los productos
        if self.empresa_id and self.producto_origen_id:
            if self.producto_origen.empresa_id != self.empresa_id:
                errors['producto_origen'] = 'El producto origen debe pertenecer a la misma empresa.'

        if errors:
            raise ValidationError(errors)

    def save(self, *args, **kwargs):
        """
        Guarda con validaciones.

        CRÍTICO: Siempre ejecutar validaciones antes de guardar.
        """
        # Heredar empresa del producto origen si no está establecida
        if self.producto_origen_id and not self.empresa_id:
            self.empresa_id = self.producto_origen.empresa_id

        update_fields = kwargs.get('update_fields')
        campos_criticos = ['producto_origen', 'producto_destino', 'tipo', 'bidireccional', 'activa', 'empresa']

        if update_fields is None or any(f in update_fields for f in campos_criticos):
            self.full_clean()

        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.producto_origen.codigo_sku} -> {self.producto_destino.codigo_sku} ({self.get_tipo_display()})"
