from django.db import models
from django.core.validators import MinValueValidator
from django.core.exceptions import ValidationError
import uuid
import os

class Categoria(models.Model):
    nombre = models.CharField(max_length=100)
    descripcion = models.TextField(blank=True, null=True)
    activa = models.BooleanField(default=True, db_index=True)
    idempotency_key = models.CharField(max_length=100, unique=True, blank=True, null=True)

    class Meta:
        verbose_name = 'Categoría'
        verbose_name_plural = 'Categorías'
        ordering = ['nombre']
        indexes = [
            models.Index(fields=['activa', 'nombre']),
        ]

    def clean(self):
        """Validaciones a nivel de modelo"""
        if self.nombre:
            self.nombre = self.nombre.strip()
            if not self.nombre:
                raise ValidationError({'nombre': 'El nombre no puede estar vacío.'})

    def __str__(self):
        return self.nombre

class Producto(models.Model):
    TIPO_PRODUCTO_CHOICES = (
        ('ALMACENABLE', 'Producto Almacenable (Inventario)'),
        ('SERVICIO', 'Servicio (Intangible)'),
        ('CONSUMIBLE', 'Consumible (Uso Interno)'),
        ('ACTIVO_FIJO', 'Activo Fijo (Maquinaria/Equipos)'),
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
        default=18.00,
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
    fecha_creacion = models.DateTimeField(auto_now_add=True)
    fecha_actualizacion = models.DateTimeField(auto_now=True)
    idempotency_key = models.CharField(max_length=100, unique=True, blank=True, null=True)

    class Meta:
        verbose_name = 'Producto'
        verbose_name_plural = 'Productos'
        ordering = ['nombre']
        indexes = [
            models.Index(fields=['activo', 'tipo_producto']),
            models.Index(fields=['codigo_sku', 'activo']),
            models.Index(fields=['-fecha_creacion']),
        ]

    def clean(self):
        """Validaciones a nivel de modelo"""
        if self.nombre:
            self.nombre = self.nombre.strip()
            if not self.nombre:
                raise ValidationError({'nombre': 'El nombre no puede estar vacío.'})
        
        if self.codigo_sku:
            self.codigo_sku = self.codigo_sku.strip()
            if not self.codigo_sku:
                raise ValidationError({'codigo_sku': 'El código SKU no puede estar vacío.'})
        
        if self.precio_venta_base < 0:
            raise ValidationError({'precio_venta_base': 'El precio de venta no puede ser negativo.'})
        
        if self.impuesto_itbis < 0 or self.impuesto_itbis > 100:
            raise ValidationError({'impuesto_itbis': 'El porcentaje de ITBIS debe estar entre 0 y 100.'})
        
        if self.porcentaje_descuento_promocional < 0 or self.porcentaje_descuento_promocional > 100:
            raise ValidationError({'porcentaje_descuento_promocional': 'El descuento promocional debe estar entre 0 y 100.'})
        
        if self.porcentaje_descuento_maximo < 0 or self.porcentaje_descuento_maximo > 100:
            raise ValidationError({'porcentaje_descuento_maximo': 'El descuento máximo debe estar entre 0 y 100.'})
        
        if self.meses_garantia < 0:
            raise ValidationError({'meses_garantia': 'Los meses de garantía no pueden ser negativos.'})
        
        # Auto-configurar control de stock basado en tipo
        if self.tipo_producto in ['SERVICIO', 'ACTIVO_FIJO']:
            self.controlar_stock = False
        
        # Si es exento, forzar ITBIS a 0
        if self.es_exento:
            self.impuesto_itbis = 0.00
        
        # Si no tiene garantía, asegurar que meses sea 0
        if not self.tiene_garantia:
            self.meses_garantia = 0

    def save(self, *args, **kwargs):
        self.full_clean()  # Llamar a clean() antes de guardar
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
    """
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

    uuid = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)
    fecha_creacion = models.DateTimeField(auto_now_add=True)
    fecha_actualizacion = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Imagen de Producto'
        verbose_name_plural = 'Imágenes de Productos'
        ordering = ['producto', 'orden', '-es_principal']
        indexes = [
            models.Index(fields=['producto', 'es_principal']),
            models.Index(fields=['producto', 'activa', 'orden']),
        ]

    def clean(self):
        """Validaciones a nivel de modelo"""
        # Si se marca como principal, desmarcar otras del mismo producto
        if self.es_principal and self.pk:
            ImagenProducto.objects.filter(
                producto=self.producto,
                es_principal=True
            ).exclude(pk=self.pk).update(es_principal=False)

    def save(self, *args, **kwargs):
        # Si es la primera imagen y no hay principal, marcarla como principal
        if not self.pk:
            existing = ImagenProducto.objects.filter(producto=self.producto)
            if not existing.exists():
                self.es_principal = True
            elif self.es_principal:
                # Desmarcar otras como principal
                existing.filter(es_principal=True).update(es_principal=False)

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
    Referencias cruzadas entre productos (productos relacionados, sustitutos, complementarios).
    """
    TIPO_REFERENCIA_CHOICES = (
        ('RELACIONADO', 'Producto Relacionado'),
        ('SUSTITUTO', 'Producto Sustituto'),
        ('COMPLEMENTARIO', 'Producto Complementario'),
        ('ACCESORIO', 'Accesorio'),
        ('REPUESTO', 'Repuesto'),
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

    uuid = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)
    fecha_creacion = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Referencia Cruzada'
        verbose_name_plural = 'Referencias Cruzadas'
        unique_together = ('producto_origen', 'producto_destino', 'tipo')
        ordering = ['producto_origen', 'tipo']

    def clean(self):
        if self.producto_origen == self.producto_destino:
            raise ValidationError({
                'producto_destino': 'El producto destino no puede ser el mismo que el origen.'
            })

    def __str__(self):
        return f"{self.producto_origen.codigo_sku} -> {self.producto_destino.codigo_sku} ({self.get_tipo_display()})"
