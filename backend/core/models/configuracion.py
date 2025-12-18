"""
Modelo de Configuración del Sistema por Empresa.

Permite personalizar la configuración de cada empresa en el sistema multi-tenant.
"""
from django.db import models
from django.conf import settings
from django.db.models.signals import post_save
from django.dispatch import receiver

from core.config import (
    DGII_CONFIG,
    FACTURACION_CONFIG,
    INVENTARIO_CONFIG,
    NOTIFICACIONES_CONFIG,
    REPORTES_CONFIG,
    COMPRAS_CONFIG,
    SEGURIDAD_CONFIG,
)

# Mapeo centralizado de secciones (DRY - evita duplicación)
CONFIG_SECTIONS = {
    'fiscal': ('config_fiscal', DGII_CONFIG),
    'facturacion': ('config_facturacion', FACTURACION_CONFIG),
    'inventario': ('config_inventario', INVENTARIO_CONFIG),
    'notificaciones': ('config_notificaciones', NOTIFICACIONES_CONFIG),
    'reportes': ('config_reportes', REPORTES_CONFIG),
    'compras': ('config_compras', COMPRAS_CONFIG),
    'seguridad': ('config_seguridad', SEGURIDAD_CONFIG),
}


class ConfiguracionEmpresa(models.Model):
    """
    Configuración específica por empresa.

    Cada empresa puede tener su propia configuración que sobrescribe
    los valores por defecto definidos en core/config.py.

    Permisos:
    - Solo usuarios con rol 'admin' pueden ver y editar
    - La configuración fiscal solo puede ser editada por superusers
    """

    empresa = models.OneToOneField(
        'empresas.Empresa',
        on_delete=models.CASCADE,
        related_name='configuracion',
        verbose_name='Empresa'
    )

    # Secciones de configuración (JSONField para flexibilidad)
    config_fiscal = models.JSONField(
        default=dict,
        verbose_name='Configuración Fiscal',
        help_text='Configuración relacionada con DGII y aspectos fiscales'
    )
    config_facturacion = models.JSONField(
        default=dict,
        verbose_name='Configuración de Facturación',
        help_text='Plazos de crédito, descuentos, numeración, etc.'
    )
    config_inventario = models.JSONField(
        default=dict,
        verbose_name='Configuración de Inventario',
        help_text='Stock mínimo, método de costeo, alertas, etc.'
    )
    config_notificaciones = models.JSONField(
        default=dict,
        verbose_name='Configuración de Notificaciones',
        help_text='Emails automáticos, alertas, recordatorios'
    )
    config_reportes = models.JSONField(
        default=dict,
        verbose_name='Configuración de Reportes',
        help_text='Paginación, formatos de exportación, caché'
    )
    config_compras = models.JSONField(
        default=dict,
        verbose_name='Configuración de Compras',
        help_text='Plazos de pago, aprobaciones, órdenes de compra'
    )
    config_seguridad = models.JSONField(
        default=dict,
        verbose_name='Configuración de Seguridad',
        help_text='Sesiones, contraseñas, intentos de login'
    )

    # Auditoría
    usuario_creacion = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='configuraciones_creadas',
        verbose_name='Creado por'
    )
    usuario_modificacion = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='configuraciones_modificadas',
        verbose_name='Modificado por'
    )
    fecha_creacion = models.DateTimeField(
        auto_now_add=True,
        verbose_name='Fecha de Creación'
    )
    fecha_actualizacion = models.DateTimeField(
        auto_now=True,
        verbose_name='Última Actualización'
    )

    class Meta:
        verbose_name = 'Configuración de Empresa'
        verbose_name_plural = 'Configuraciones de Empresas'
        permissions = [
            ('view_config_fiscal', 'Puede ver configuración fiscal'),
            ('change_config_fiscal', 'Puede cambiar configuración fiscal'),
            ('view_config_facturacion', 'Puede ver configuración de facturación'),
            ('change_config_facturacion', 'Puede cambiar configuración de facturación'),
            ('view_config_inventario', 'Puede ver configuración de inventario'),
            ('change_config_inventario', 'Puede cambiar configuración de inventario'),
            ('view_config_notificaciones', 'Puede ver configuración de notificaciones'),
            ('change_config_notificaciones', 'Puede cambiar configuración de notificaciones'),
            ('view_config_reportes', 'Puede ver configuración de reportes'),
            ('change_config_reportes', 'Puede cambiar configuración de reportes'),
            ('view_config_compras', 'Puede ver configuración de compras'),
            ('change_config_compras', 'Puede cambiar configuración de compras'),
            ('view_config_seguridad', 'Puede ver configuración de seguridad'),
            ('change_config_seguridad', 'Puede cambiar configuración de seguridad'),
            ('restablecer_configuracion', 'Puede restablecer configuración a valores por defecto'),
        ]

    def __str__(self):
        return f"Configuración - {self.empresa.nombre}"

    def save(self, *args, **kwargs):
        """Asegura que las secciones vacías tengan valores por defecto."""
        for seccion, (campo, defaults) in CONFIG_SECTIONS.items():
            if not getattr(self, campo):
                setattr(self, campo, defaults.copy())
        super().save(*args, **kwargs)

    def restablecer_seccion(self, seccion: str) -> bool:
        """
        Restablece una sección específica a sus valores por defecto.

        Args:
            seccion: Nombre de la sección (fiscal, facturacion, etc.)

        Returns:
            True si se restableció correctamente, False si la sección no existe
        """
        if seccion not in CONFIG_SECTIONS:
            return False

        campo, defaults = CONFIG_SECTIONS[seccion]
        setattr(self, campo, defaults.copy())
        self.save(update_fields=[campo, 'fecha_actualizacion'])
        return True

    def restablecer_todo(self):
        """Restablece todas las secciones a sus valores por defecto."""
        for seccion, (campo, defaults) in CONFIG_SECTIONS.items():
            setattr(self, campo, defaults.copy())
        self.save()

    def get_valor(self, seccion: str, clave: str, default=None):
        """
        Obtiene un valor específico de configuración.

        Args:
            seccion: Nombre de la sección
            clave: Clave dentro de la sección
            default: Valor por defecto si no existe

        Returns:
            El valor configurado o el default
        """
        if seccion not in CONFIG_SECTIONS:
            return default

        campo, _ = CONFIG_SECTIONS[seccion]
        config = getattr(self, campo, {})
        return config.get(clave, default)

    def set_valor(self, seccion: str, clave: str, valor) -> bool:
        """
        Establece un valor específico de configuración.

        Args:
            seccion: Nombre de la sección
            clave: Clave dentro de la sección
            valor: Nuevo valor

        Returns:
            True si se estableció correctamente
        """
        if seccion not in CONFIG_SECTIONS:
            return False

        campo, _ = CONFIG_SECTIONS[seccion]
        config = getattr(self, campo)
        config[clave] = valor
        setattr(self, campo, config)
        self.save(update_fields=[campo, 'fecha_actualizacion'])
        return True


# =============================================================================
# SIGNAL: Crear configuración automáticamente al crear empresa
# =============================================================================
@receiver(post_save, sender='empresas.Empresa')
def crear_configuracion_empresa(sender, instance, created, **kwargs):
    """
    Crea automáticamente la configuración cuando se crea una nueva empresa.
    """
    if created:
        defaults = {campo: config.copy() for _, (campo, config) in CONFIG_SECTIONS.items()}
        ConfiguracionEmpresa.objects.get_or_create(
            empresa=instance,
            defaults=defaults
        )
