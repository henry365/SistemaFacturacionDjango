"""
Serializers para DGII (Comprobantes Fiscales)

Incluye validación de empresa en relaciones para garantizar
aislamiento multi-tenant.
"""
from rest_framework import serializers
from .models import TipoComprobante, SecuenciaNCF
from .constants import ERROR_TIPO_COMPROBANTE_OTRA_EMPRESA


class TipoComprobanteSerializer(serializers.ModelSerializer):
    """Serializer para TipoComprobante"""
    ncf_ejemplo = serializers.SerializerMethodField()
    usuario_creacion_nombre = serializers.CharField(
        source='usuario_creacion.username',
        read_only=True,
        allow_null=True
    )
    usuario_modificacion_nombre = serializers.CharField(
        source='usuario_modificacion.username',
        read_only=True,
        allow_null=True
    )

    class Meta:
        model = TipoComprobante
        fields = [
            'id', 'empresa', 'codigo', 'nombre', 'prefijo', 'activo',
            'uuid', 'fecha_creacion', 'fecha_actualizacion', 'ncf_ejemplo',
            'usuario_creacion', 'usuario_modificacion',
            'usuario_creacion_nombre', 'usuario_modificacion_nombre'
        ]
        read_only_fields = [
            'uuid', 'fecha_creacion', 'fecha_actualizacion', 'empresa',
            'usuario_creacion', 'usuario_modificacion'
        ]

    def get_ncf_ejemplo(self, obj):
        """Retorna ejemplo de formato NCF"""
        return f"{obj.prefijo}{obj.codigo}00000001"


class TipoComprobanteListSerializer(serializers.ModelSerializer):
    """Serializer optimizado para listados"""
    ncf_ejemplo = serializers.SerializerMethodField()

    class Meta:
        model = TipoComprobante
        fields = ['id', 'codigo', 'nombre', 'prefijo', 'activo', 'ncf_ejemplo']

    def get_ncf_ejemplo(self, obj):
        return f"{obj.prefijo}{obj.codigo}00000001"


class SecuenciaNCFSerializer(serializers.ModelSerializer):
    """Serializer para SecuenciaNCF"""
    tipo_comprobante_nombre = serializers.CharField(
        source='tipo_comprobante.__str__', read_only=True
    )
    tipo_comprobante_codigo = serializers.CharField(
        source='tipo_comprobante.codigo', read_only=True
    )
    disponibles = serializers.IntegerField(read_only=True)
    porcentaje_uso = serializers.FloatField(read_only=True)
    proximo_ncf = serializers.SerializerMethodField()
    usuario_creacion_nombre = serializers.CharField(
        source='usuario_creacion.username',
        read_only=True,
        allow_null=True
    )
    usuario_modificacion_nombre = serializers.CharField(
        source='usuario_modificacion.username',
        read_only=True,
        allow_null=True
    )

    class Meta:
        model = SecuenciaNCF
        fields = [
            'id', 'empresa', 'tipo_comprobante', 'tipo_comprobante_nombre',
            'tipo_comprobante_codigo', 'descripcion',
            'secuencia_inicial', 'secuencia_final', 'secuencia_actual',
            'fecha_vencimiento', 'alerta_cantidad', 'activo', 'agotada',
            'disponibles', 'porcentaje_uso', 'proximo_ncf',
            'uuid', 'fecha_creacion', 'fecha_actualizacion',
            'usuario_creacion', 'usuario_modificacion',
            'usuario_creacion_nombre', 'usuario_modificacion_nombre'
        ]
        read_only_fields = [
            'uuid', 'fecha_creacion', 'fecha_actualizacion',
            'usuario_creacion', 'usuario_modificacion', 'secuencia_actual', 'empresa'
        ]

    def get_proximo_ncf(self, obj):
        """Retorna el proximo NCF que se generara"""
        if obj.agotada:
            return None
        return obj.siguiente_numero()

    def validate_tipo_comprobante(self, value):
        """
        Valida que el tipo_comprobante pertenezca a la misma empresa del usuario.

        CRÍTICO: Garantiza aislamiento multi-tenant.
        """
        request = self.context.get('request')
        if request and hasattr(request.user, 'empresa'):
            user_empresa = request.user.empresa
            if value.empresa is not None and user_empresa is not None:
                if value.empresa != user_empresa:
                    raise serializers.ValidationError(
                        ERROR_TIPO_COMPROBANTE_OTRA_EMPRESA
                    )
        return value

    def validate(self, data):
        """Validaciones personalizadas"""
        secuencia_inicial = data.get('secuencia_inicial')
        secuencia_final = data.get('secuencia_final')

        if secuencia_inicial and secuencia_final:
            if secuencia_inicial >= secuencia_final:
                raise serializers.ValidationError({
                    'secuencia_final': 'La secuencia final debe ser mayor que la inicial.'
                })

        return data


class SecuenciaNCFListSerializer(serializers.ModelSerializer):
    """Serializer optimizado para listados"""
    tipo_comprobante_nombre = serializers.CharField(
        source='tipo_comprobante.__str__', read_only=True
    )
    disponibles = serializers.IntegerField(read_only=True)
    porcentaje_uso = serializers.FloatField(read_only=True)

    class Meta:
        model = SecuenciaNCF
        fields = [
            'id', 'tipo_comprobante', 'tipo_comprobante_nombre',
            'descripcion', 'secuencia_actual', 'secuencia_final',
            'fecha_vencimiento', 'activo', 'agotada',
            'disponibles', 'porcentaje_uso'
        ]


class GenerarNCFSerializer(serializers.Serializer):
    """Serializer para generar un NCF"""
    tipo_comprobante_id = serializers.IntegerField(required=True)

    def validate_tipo_comprobante_id(self, value):
        """Valida que exista secuencia activa para el tipo"""
        request = self.context.get('request')
        if request and hasattr(request.user, 'empresa'):
            empresa = request.user.empresa
            secuencia = SecuenciaNCF.objects.filter(
                empresa=empresa,
                tipo_comprobante_id=value,
                activo=True
            ).first()
            if not secuencia:
                raise serializers.ValidationError(
                    'No hay secuencia activa para este tipo de comprobante.'
                )
            if secuencia.agotada:
                raise serializers.ValidationError(
                    'La secuencia de este tipo de comprobante está agotada.'
                )
        return value
