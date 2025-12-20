"""
Serializers para el módulo Empresas
"""
import re
from rest_framework import serializers
from .models import Empresa
from .constants import (
    LONGITUD_RNC_MIN, LONGITUD_RNC_MAX,
    LONGITUD_TELEFONO_MIN, LONGITUD_TELEFONO_MAX,
    ERROR_RNC_FORMATO, ERROR_RNC_LONGITUD, ERROR_RNC_DUPLICADO,
    ERROR_TELEFONO_FORMATO, ERROR_TELEFONO_LONGITUD,
    ERROR_CONFIGURACION_FISCAL_INVALIDA, ERROR_NOMBRE_VACIO
)


class EmpresaListSerializer(serializers.ModelSerializer):
    """
    Serializer optimizado para listado de empresas.

    Incluye solo campos esenciales para mejorar performance en listas.
    """

    class Meta:
        model = Empresa
        fields = [
            'id', 'uuid', 'nombre', 'rnc', 'telefono', 'activo',
            'fecha_creacion', 'fecha_actualizacion'
        ]
        read_only_fields = fields


class EmpresaSerializer(serializers.ModelSerializer):
    """
    Serializer completo para el modelo Empresa.

    Usado para detalle, creación y actualización.
    """

    class Meta:
        model = Empresa
        fields = '__all__'
        read_only_fields = ('id', 'uuid', 'fecha_creacion', 'fecha_actualizacion')

    def validate_rnc(self, value):
        """Validar formato de RNC (solo números y guiones)"""
        if value:
            # RNC puede tener formato: 123456789 o 123-45678-9
            if not re.match(r'^[\d-]+$', value):
                raise serializers.ValidationError(ERROR_RNC_FORMATO)

            # Remover guiones para validar longitud
            rnc_sin_guiones = value.replace('-', '')
            if len(rnc_sin_guiones) < LONGITUD_RNC_MIN or len(rnc_sin_guiones) > LONGITUD_RNC_MAX:
                raise serializers.ValidationError(ERROR_RNC_LONGITUD)

        return value

    def validate_telefono(self, value):
        """Validar formato de teléfono"""
        if value:
            # Teléfono puede tener formato: 809-555-1234 o (809) 555-1234 o 8095551234
            if not re.match(r'^[\d\s\-\(\)]+$', value):
                raise serializers.ValidationError(ERROR_TELEFONO_FORMATO)

            # Remover caracteres especiales para validar longitud
            telefono_sin_formato = re.sub(r'[\s\-\(\)]', '', value)
            if len(telefono_sin_formato) < LONGITUD_TELEFONO_MIN or len(telefono_sin_formato) > LONGITUD_TELEFONO_MAX:
                raise serializers.ValidationError(ERROR_TELEFONO_LONGITUD)

        return value

    def validate_configuracion_fiscal(self, value):
        """Validar que configuracion_fiscal sea un diccionario válido"""
        if value and not isinstance(value, dict):
            raise serializers.ValidationError(ERROR_CONFIGURACION_FISCAL_INVALIDA)
        return value

    def validate(self, data):
        """Validaciones de negocio personalizadas"""
        # Validar que el nombre no esté vacío
        nombre = data.get('nombre', '')
        if not nombre or not nombre.strip():
            raise serializers.ValidationError({"nombre": ERROR_NOMBRE_VACIO})

        # Validar RNC único (excepto si es actualización del mismo registro)
        rnc = data.get('rnc')
        if rnc:
            queryset = Empresa.objects.filter(rnc=rnc)
            if self.instance:
                queryset = queryset.exclude(pk=self.instance.pk)
            if queryset.exists():
                raise serializers.ValidationError({
                    "rnc": ERROR_RNC_DUPLICADO
                })

        return data
