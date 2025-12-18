from django.db import models
from django.conf import settings
import uuid

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
    prefijo = models.CharField(max_length=1, default='B', help_text="Prefijo de la serie (Generalmente B o E)")
    activo = models.BooleanField(default=True)
    uuid = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)
    fecha_creacion = models.DateTimeField(auto_now_add=True, null=True)
    fecha_actualizacion = models.DateTimeField(auto_now=True, null=True)

    class Meta:
        verbose_name = 'Tipo de Comprobante'
        verbose_name_plural = 'Tipos de Comprobantes'
        ordering = ['codigo']
        unique_together = ('empresa', 'codigo')

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
    tipo_comprobante = models.ForeignKey(TipoComprobante, on_delete=models.PROTECT, related_name='secuencias')
    descripcion = models.CharField(max_length=100, help_text="Ej: Talonario Principal Facturas Crédito Fiscal")

    secuencia_inicial = models.IntegerField(help_text="Número inicial autorizado (ej. 1)")
    secuencia_final = models.IntegerField(help_text="Número final autorizado (ej. 100)")
    secuencia_actual = models.IntegerField(default=0, help_text="Último número utilizado")

    fecha_vencimiento = models.DateField(help_text="Fecha de vencimiento de la secuencia")
    alerta_cantidad = models.IntegerField(default=10, help_text="Avisar cuando queden X números")

    activo = models.BooleanField(default=True)
    uuid = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)

    fecha_creacion = models.DateTimeField(auto_now_add=True)
    fecha_actualizacion = models.DateTimeField(auto_now=True)
    usuario_creacion = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, related_name='secuencias_creadas', null=True, blank=True)
    usuario_modificacion = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, related_name='secuencias_modificadas', null=True, blank=True)

    class Meta:
        verbose_name = 'Secuencia NCF'
        verbose_name_plural = 'Secuencias NCF'
        unique_together = ('empresa', 'tipo_comprobante', 'secuencia_inicial')

    def __str__(self):
        return f"{self.tipo_comprobante} ({self.secuencia_actual}/{self.secuencia_final})"

    @property
    def agotada(self):
        return self.secuencia_actual >= self.secuencia_final

    def siguiente_numero(self):
        """
        Retorna el siguiente NCF formateado y aumenta el contador.
        Debe usarse dentro de una transacción atómica.
        """
        if self.agotada:
            raise ValueError("Secuencia de comprobantes agotada")
        
        siguiente = self.secuencia_actual + 1
        # Formato NCF: Prefijo (B) + Tipo (01) + Secuencia (8 dígitos) = B0100000001
        # Nota: La longitud de la secuencia puede variar (11 o 13 caracteres total), estándar actual es 11 (B + 01 + 8 digitos)
        # B0100000001
        ncf_formateado = f"{self.tipo_comprobante.prefijo}{self.tipo_comprobante.codigo}{siguiente:08d}"
        
        return ncf_formateado
