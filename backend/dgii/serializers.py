"""
Serializers para DGII (Comprobantes Fiscales)
"""
from rest_framework import serializers
from .models import TipoComprobante, SecuenciaNCF


class TipoComprobanteSerializer(serializers.ModelSerializer):
    """Serializer para TipoComprobante"""
    ncf_ejemplo = serializers.SerializerMethodField()

    class Meta:
        model = TipoComprobante
        fields = [
            'id', 'empresa', 'codigo', 'nombre', 'prefijo', 'activo',
            'uuid', 'fecha_creacion', 'fecha_actualizacion', 'ncf_ejemplo'
        ]
        read_only_fields = ['uuid', 'fecha_creacion', 'fecha_actualizacion', 'empresa']

    def get_ncf_ejemplo(self, obj):
        """Retorna ejemplo de formato NCF"""
        return f"{obj.prefijo}{obj.codigo}00000001"


class SecuenciaNCFSerializer(serializers.ModelSerializer):
    """Serializer para SecuenciaNCF"""
    tipo_comprobante_nombre = serializers.CharField(
        source='tipo_comprobante.__str__', read_only=True
    )
    disponibles = serializers.SerializerMethodField()
    porcentaje_uso = serializers.SerializerMethodField()
    proximo_ncf = serializers.SerializerMethodField()

    class Meta:
        model = SecuenciaNCF
        fields = [
            'id', 'empresa', 'tipo_comprobante', 'tipo_comprobante_nombre',
            'descripcion', 'secuencia_inicial', 'secuencia_final', 'secuencia_actual',
            'fecha_vencimiento', 'alerta_cantidad', 'activo', 'agotada',
            'disponibles', 'porcentaje_uso', 'proximo_ncf',
            'uuid', 'fecha_creacion', 'fecha_actualizacion',
            'usuario_creacion', 'usuario_modificacion'
        ]
        read_only_fields = [
            'uuid', 'fecha_creacion', 'fecha_actualizacion',
            'usuario_creacion', 'usuario_modificacion', 'secuencia_actual', 'empresa'
        ]

    def get_disponibles(self, obj):
        """Retorna cantidad de NCF disponibles"""
        return obj.secuencia_final - obj.secuencia_actual

    def get_porcentaje_uso(self, obj):
        """Retorna porcentaje de uso de la secuencia"""
        total = obj.secuencia_final - obj.secuencia_inicial + 1
        usados = obj.secuencia_actual - obj.secuencia_inicial + 1
        if total > 0:
            return round((usados / total) * 100, 2)
        return 0

    def get_proximo_ncf(self, obj):
        """Retorna el proximo NCF que se generara"""
        if obj.agotada:
            return None
        return obj.siguiente_numero()

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
                    'La secuencia de este tipo de comprobante esta agotada.'
                )
        return value
