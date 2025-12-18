"""
Serializers para Activos Fijos
"""
from rest_framework import serializers
from .models import TipoActivo, ActivoFijo, Depreciacion


class TipoActivoSerializer(serializers.ModelSerializer):
    """Serializer para TipoActivo"""

    class Meta:
        model = TipoActivo
        fields = [
            'id', 'empresa', 'nombre', 'descripcion',
            'porcentaje_depreciacion_anual', 'vida_util_anos', 'activo',
            'uuid', 'fecha_creacion', 'fecha_actualizacion'
        ]
        read_only_fields = ['uuid', 'fecha_creacion', 'fecha_actualizacion', 'empresa']


class ActivoFijoSerializer(serializers.ModelSerializer):
    """Serializer para ActivoFijo"""
    tipo_activo_nombre = serializers.CharField(source='tipo_activo.nombre', read_only=True)
    responsable_nombre = serializers.CharField(source='responsable.username', read_only=True)
    depreciacion_acumulada = serializers.DecimalField(
        max_digits=14, decimal_places=2, read_only=True
    )
    porcentaje_depreciado = serializers.DecimalField(
        max_digits=5, decimal_places=2, read_only=True
    )

    class Meta:
        model = ActivoFijo
        fields = [
            'id', 'empresa', 'tipo_activo', 'tipo_activo_nombre',
            'producto_origen', 'compra_origen', 'detalle_compra_origen',
            'codigo_interno', 'nombre', 'descripcion', 'marca', 'modelo', 'serial',
            'ubicacion_fisica', 'responsable', 'responsable_nombre',
            'fecha_adquisicion', 'valor_adquisicion', 'valor_libro_actual',
            'depreciacion_acumulada', 'porcentaje_depreciado',
            'estado', 'especificaciones',
            'uuid', 'fecha_creacion', 'fecha_actualizacion',
            'usuario_creacion', 'usuario_modificacion'
        ]
        read_only_fields = [
            'uuid', 'fecha_creacion', 'fecha_actualizacion',
            'usuario_creacion', 'usuario_modificacion', 'empresa'
        ]


class ActivoFijoListSerializer(serializers.ModelSerializer):
    """Serializer simplificado para listados de activos"""
    tipo_activo_nombre = serializers.CharField(source='tipo_activo.nombre', read_only=True)

    class Meta:
        model = ActivoFijo
        fields = [
            'id', 'codigo_interno', 'nombre', 'tipo_activo_nombre',
            'marca', 'modelo', 'estado', 'valor_adquisicion', 'valor_libro_actual',
            'fecha_adquisicion', 'ubicacion_fisica'
        ]


class DepreciacionSerializer(serializers.ModelSerializer):
    """Serializer para Depreciacion"""
    activo_codigo = serializers.CharField(source='activo.codigo_interno', read_only=True)
    activo_nombre = serializers.CharField(source='activo.nombre', read_only=True)

    class Meta:
        model = Depreciacion
        fields = [
            'id', 'activo', 'activo_codigo', 'activo_nombre',
            'fecha', 'monto', 'valor_libro_anterior', 'valor_libro_nuevo',
            'observacion', 'uuid', 'fecha_creacion', 'usuario_creacion'
        ]
        read_only_fields = ['uuid', 'fecha_creacion', 'usuario_creacion']

    def validate(self, data):
        """Valida que los valores de libro sean consistentes"""
        monto = data.get('monto')
        valor_anterior = data.get('valor_libro_anterior')
        valor_nuevo = data.get('valor_libro_nuevo')

        if monto and valor_anterior and valor_nuevo:
            expected_nuevo = valor_anterior - monto
            if abs(valor_nuevo - expected_nuevo) > 0.01:
                raise serializers.ValidationError({
                    'valor_libro_nuevo': f'El valor libro nuevo debe ser {expected_nuevo} (anterior - monto).'
                })

        return data


class CalcularDepreciacionSerializer(serializers.Serializer):
    """Serializer para calcular depreciacion de un activo"""
    fecha = serializers.DateField()
    observacion = serializers.CharField(required=False, allow_blank=True, max_length=255)
