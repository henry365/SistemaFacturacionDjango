"""
Serializers para el módulo de Configuración del Sistema.

Estos serializers manejan la validación y serialización de la
configuración de empresa con restricciones por rol de usuario.
"""
from rest_framework import serializers
from .models import ConfiguracionEmpresa
from .config import (
    DGII_CONFIG,
    FACTURACION_CONFIG,
    INVENTARIO_CONFIG,
    NOTIFICACIONES_CONFIG,
    REPORTES_CONFIG,
    COMPRAS_CONFIG,
    SEGURIDAD_CONFIG,
)


class ConfiguracionSeccionSerializer(serializers.Serializer):
    """
    Serializer base para secciones de configuración.
    Valida que solo se envíen claves válidas.
    """
    pass


class ConfiguracionFiscalSerializer(serializers.Serializer):
    """Serializer para la sección fiscal (solo lectura para no-superusers)."""
    ITBIS_TASA = serializers.FloatField(required=False, min_value=0, max_value=1)
    ITBIS_TASA_REDUCIDA = serializers.FloatField(required=False, min_value=0, max_value=1)
    RETENCION_ISR_SERVICIOS = serializers.FloatField(required=False, min_value=0, max_value=1)
    RETENCION_ISR_ALQUILERES = serializers.FloatField(required=False, min_value=0, max_value=1)
    RETENCION_ITBIS = serializers.FloatField(required=False, min_value=0, max_value=1)


class ConfiguracionFacturacionSerializer(serializers.Serializer):
    """Serializer para la sección de facturación."""
    DIAS_CREDITO_DEFAULT = serializers.IntegerField(required=False, min_value=0, max_value=365)
    DIAS_ALERTA_VENCIMIENTO = serializers.IntegerField(required=False, min_value=1, max_value=90)
    MONEDA_DEFAULT = serializers.ChoiceField(
        required=False,
        choices=[('DOP', 'DOP'), ('USD', 'USD'), ('EUR', 'EUR')]
    )
    DESCUENTO_MAXIMO_PORCENTAJE = serializers.FloatField(
        required=False, min_value=0, max_value=100
    )
    PERMITIR_DESCUENTO_FACTURA = serializers.BooleanField(required=False)


class ConfiguracionInventarioSerializer(serializers.Serializer):
    """Serializer para la sección de inventario."""
    STOCK_MINIMO_DEFAULT = serializers.IntegerField(required=False, min_value=0)
    STOCK_MAXIMO_DEFAULT = serializers.IntegerField(required=False, min_value=1)
    METODO_COSTEO = serializers.ChoiceField(
        required=False,
        choices=[('PROMEDIO', 'Promedio'), ('PEPS', 'PEPS'), ('UEPS', 'UEPS')]
    )
    PERMITIR_STOCK_NEGATIVO = serializers.BooleanField(required=False)
    VALIDAR_STOCK_EN_FACTURACION = serializers.BooleanField(required=False)
    HABILITAR_ALERTAS_STOCK = serializers.BooleanField(required=False)
    PORCENTAJE_STOCK_CRITICO = serializers.IntegerField(
        required=False, min_value=1, max_value=100
    )
    USAR_LOTES = serializers.BooleanField(required=False)
    ALERTAR_VENCIMIENTO_DIAS = serializers.IntegerField(required=False, min_value=1, max_value=365)


class ConfiguracionNotificacionesSerializer(serializers.Serializer):
    """Serializer para la sección de notificaciones."""
    HABILITAR_EMAIL_FACTURA = serializers.BooleanField(required=False)
    HABILITAR_EMAIL_COTIZACION = serializers.BooleanField(required=False)
    HABILITAR_EMAIL_NOTA_CREDITO = serializers.BooleanField(required=False)
    HABILITAR_EMAIL_CXC_VENCIDA = serializers.BooleanField(required=False)
    HABILITAR_EMAIL_CXC_POR_VENCER = serializers.BooleanField(required=False)
    DIAS_ANTES_VENCIMIENTO_EMAIL = serializers.IntegerField(
        required=False, min_value=1, max_value=30
    )
    HABILITAR_EMAIL_STOCK_BAJO = serializers.BooleanField(required=False)
    HABILITAR_EMAIL_STOCK_CRITICO = serializers.BooleanField(required=False)
    DIAS_ENTRE_RECORDATORIOS = serializers.IntegerField(
        required=False, min_value=1, max_value=30
    )
    MAX_RECORDATORIOS = serializers.IntegerField(required=False, min_value=1, max_value=10)


class ConfiguracionReportesSerializer(serializers.Serializer):
    """Serializer para la sección de reportes."""
    PAGE_SIZE_DEFAULT = serializers.IntegerField(required=False, min_value=10, max_value=500)
    PAGE_SIZE_MAX = serializers.IntegerField(required=False, min_value=100, max_value=1000)
    FORMATO_EXPORTACION_DEFAULT = serializers.ChoiceField(
        required=False,
        choices=[('xlsx', 'Excel'), ('csv', 'CSV'), ('pdf', 'PDF')]
    )
    CACHE_REPORTES_SEGUNDOS = serializers.IntegerField(
        required=False, min_value=0, max_value=3600
    )
    HABILITAR_CACHE_REPORTES = serializers.BooleanField(required=False)


class ConfiguracionComprasSerializer(serializers.Serializer):
    """Serializer para la sección de compras."""
    DIAS_PAGO_DEFAULT = serializers.IntegerField(required=False, min_value=0, max_value=365)
    DIAS_ALERTA_PAGO = serializers.IntegerField(required=False, min_value=1, max_value=30)
    REQUIERE_APROBACION = serializers.BooleanField(required=False)
    MONTO_MINIMO_APROBACION = serializers.FloatField(required=False, min_value=0)
    PERMITIR_RECEPCION_PARCIAL = serializers.BooleanField(required=False)
    DIAS_MAX_RECEPCION = serializers.IntegerField(required=False, min_value=1, max_value=365)


class ConfiguracionSeguridadSerializer(serializers.Serializer):
    """Serializer para la sección de seguridad."""
    TIEMPO_SESION_MINUTOS = serializers.IntegerField(
        required=False, min_value=5, max_value=1440
    )
    CERRAR_SESION_INACTIVIDAD = serializers.BooleanField(required=False)
    MINUTOS_INACTIVIDAD = serializers.IntegerField(required=False, min_value=5, max_value=120)
    LONGITUD_MINIMA_PASSWORD = serializers.IntegerField(
        required=False, min_value=6, max_value=32
    )
    REQUIERE_MAYUSCULAS = serializers.BooleanField(required=False)
    REQUIERE_NUMEROS = serializers.BooleanField(required=False)
    REQUIERE_ESPECIALES = serializers.BooleanField(required=False)
    MAX_INTENTOS_LOGIN = serializers.IntegerField(required=False, min_value=3, max_value=10)
    BLOQUEO_MINUTOS = serializers.IntegerField(required=False, min_value=5, max_value=60)


class ConfiguracionEmpresaSerializer(serializers.ModelSerializer):
    """
    Serializer principal para ConfiguracionEmpresa.

    Incluye validación de permisos por sección:
    - config_fiscal: Solo superusers pueden modificar
    - Otras secciones: Solo admins pueden modificar
    """
    empresa_nombre = serializers.CharField(source='empresa.nombre', read_only=True)
    usuario_creacion_nombre = serializers.CharField(
        source='usuario_creacion.username', read_only=True
    )
    usuario_modificacion_nombre = serializers.CharField(
        source='usuario_modificacion.username', read_only=True
    )

    class Meta:
        model = ConfiguracionEmpresa
        fields = [
            'id',
            'empresa',
            'empresa_nombre',
            'config_fiscal',
            'config_facturacion',
            'config_inventario',
            'config_notificaciones',
            'config_reportes',
            'config_compras',
            'config_seguridad',
            'usuario_creacion',
            'usuario_creacion_nombre',
            'usuario_modificacion',
            'usuario_modificacion_nombre',
            'fecha_creacion',
            'fecha_actualizacion',
        ]
        read_only_fields = [
            'id',
            'empresa',
            'usuario_creacion',
            'fecha_creacion',
            'fecha_actualizacion',
        ]

    def validate_config_fiscal(self, value):
        """Solo superusers pueden modificar la configuración fiscal."""
        request = self.context.get('request')
        if request and not request.user.is_superuser:
            # No permitir cambios, mantener valor actual
            if self.instance:
                return self.instance.config_fiscal
            return DGII_CONFIG.copy()
        return value

    def validate(self, attrs):
        """Validación general."""
        # Validar que PAGE_SIZE_MAX >= PAGE_SIZE_DEFAULT en reportes
        config_reportes = attrs.get('config_reportes', {})
        if config_reportes:
            default_size = config_reportes.get('PAGE_SIZE_DEFAULT', 100)
            max_size = config_reportes.get('PAGE_SIZE_MAX', 500)
            if default_size > max_size:
                raise serializers.ValidationError({
                    'config_reportes': 'PAGE_SIZE_DEFAULT no puede ser mayor que PAGE_SIZE_MAX'
                })

        return attrs

    def update(self, instance, validated_data):
        """Actualiza la configuración y registra el usuario que modifica."""
        request = self.context.get('request')
        if request and request.user:
            validated_data['usuario_modificacion'] = request.user
        return super().update(instance, validated_data)


class ConfiguracionEmpresaResumenSerializer(serializers.ModelSerializer):
    """Serializer resumido para listados."""
    empresa_nombre = serializers.CharField(source='empresa.nombre', read_only=True)

    class Meta:
        model = ConfiguracionEmpresa
        fields = [
            'id',
            'empresa',
            'empresa_nombre',
            'fecha_actualizacion',
        ]


class RestablecerSeccionSerializer(serializers.Serializer):
    """Serializer para restablecer una sección específica."""
    seccion = serializers.ChoiceField(
        choices=[
            ('fiscal', 'Fiscal'),
            ('facturacion', 'Facturación'),
            ('inventario', 'Inventario'),
            ('notificaciones', 'Notificaciones'),
            ('reportes', 'Reportes'),
            ('compras', 'Compras'),
            ('seguridad', 'Seguridad'),
            ('todo', 'Todas las secciones'),
        ]
    )


class ActualizarSeccionSerializer(serializers.Serializer):
    """Serializer para actualizar una sección específica."""
    seccion = serializers.ChoiceField(
        choices=[
            ('fiscal', 'Fiscal'),
            ('facturacion', 'Facturación'),
            ('inventario', 'Inventario'),
            ('notificaciones', 'Notificaciones'),
            ('reportes', 'Reportes'),
            ('compras', 'Compras'),
            ('seguridad', 'Seguridad'),
        ]
    )
    valores = serializers.JSONField()

    def validate(self, attrs):
        """Valida los valores según la sección."""
        seccion = attrs['seccion']
        valores = attrs['valores']

        # Mapeo de secciones a sus serializers
        serializers_map = {
            'fiscal': ConfiguracionFiscalSerializer,
            'facturacion': ConfiguracionFacturacionSerializer,
            'inventario': ConfiguracionInventarioSerializer,
            'notificaciones': ConfiguracionNotificacionesSerializer,
            'reportes': ConfiguracionReportesSerializer,
            'compras': ConfiguracionComprasSerializer,
            'seguridad': ConfiguracionSeguridadSerializer,
        }

        serializer_class = serializers_map.get(seccion)
        if serializer_class:
            serializer = serializer_class(data=valores)
            if not serializer.is_valid():
                raise serializers.ValidationError({
                    'valores': serializer.errors
                })

        return attrs
