"""
Serializers para el módulo Proveedores

Este módulo contiene los serializers para gestión de proveedores
con validaciones de negocio.
"""
from rest_framework import serializers
from django.core.validators import validate_email
from django.core.exceptions import ValidationError
import re

from .models import Proveedor
from .constants import (
    TIPO_IDENTIFICACION_RNC,
    ERROR_EMAIL_INVALIDO,
    ERROR_TELEFONO_INVALIDO,
    ERROR_TELEFONO_LONGITUD,
    ERROR_RNC_REQUERIDO,
    ERROR_NUMERO_IDENTIFICACION_DUPLICADO,
    REGEX_TELEFONO,
)


class ProveedorSerializer(serializers.ModelSerializer):
    """
    Serializer completo para Proveedor.

    Incluye todos los campos y validaciones para crear/actualizar.
    """
    empresa_nombre = serializers.ReadOnlyField(source='empresa.nombre')
    tipo_identificacion_display = serializers.CharField(
        source='get_tipo_identificacion_display',
        read_only=True
    )
    tipo_contribuyente_display = serializers.CharField(
        source='get_tipo_contribuyente_display',
        read_only=True
    )

    class Meta:
        model = Proveedor
        fields = [
            'id', 'uuid', 'empresa', 'empresa_nombre',
            'nombre', 'tipo_identificacion', 'tipo_identificacion_display',
            'numero_identificacion', 'tipo_contribuyente', 'tipo_contribuyente_display',
            'telefono', 'correo_electronico', 'direccion',
            'es_internacional', 'activo',
            'fecha_creacion', 'fecha_actualizacion',
            'usuario_creacion', 'usuario_modificacion',
            'idempotency_key'
        ]
        read_only_fields = [
            'id', 'uuid', 'empresa', 'fecha_creacion', 'fecha_actualizacion',
            'usuario_creacion', 'usuario_modificacion'
        ]

    def validate_correo_electronico(self, value):
        """Validar formato de correo electrónico"""
        if value:
            try:
                validate_email(value)
            except ValidationError:
                raise serializers.ValidationError(ERROR_EMAIL_INVALIDO)
        return value

    def validate_telefono(self, value):
        """Validar formato de teléfono"""
        if value:
            # Teléfono puede tener formato: 809-555-1234 o (809) 555-1234 o 8095551234
            if not re.match(REGEX_TELEFONO, value):
                raise serializers.ValidationError(ERROR_TELEFONO_INVALIDO)

            # Remover caracteres especiales para validar longitud
            telefono_sin_formato = re.sub(r'[\s\-\(\)]', '', value)
            if len(telefono_sin_formato) < 10 or len(telefono_sin_formato) > 15:
                raise serializers.ValidationError(ERROR_TELEFONO_LONGITUD)
        return value

    def validate(self, data):
        """Validaciones de negocio personalizadas"""
        # Validar RNC obligatorio cuando tipo_identificacion es RNC
        if data.get('tipo_identificacion') == TIPO_IDENTIFICACION_RNC and not data.get('numero_identificacion'):
            raise serializers.ValidationError({
                "numero_identificacion": ERROR_RNC_REQUERIDO
            })

        # Validar número de identificación único por empresa
        numero_identificacion = data.get('numero_identificacion')
        if numero_identificacion:
            # Obtener empresa del contexto (asignada por EmpresaAuditMixin) o de la instancia
            request = self.context.get('request')
            empresa = None
            if request and hasattr(request.user, 'empresa'):
                empresa = request.user.empresa
            elif self.instance:
                empresa = self.instance.empresa

            if empresa:
                queryset = Proveedor.objects.filter(
                    empresa=empresa,
                    numero_identificacion=numero_identificacion
                )
                if self.instance:
                    queryset = queryset.exclude(pk=self.instance.pk)
                if queryset.exists():
                    raise serializers.ValidationError({
                        "numero_identificacion": ERROR_NUMERO_IDENTIFICACION_DUPLICADO
                    })

        return data


class ProveedorListSerializer(serializers.ModelSerializer):
    """
    Serializer optimizado para listado de Proveedores.

    Incluye solo campos esenciales para mejorar rendimiento en listados.
    """
    tipo_identificacion_display = serializers.CharField(
        source='get_tipo_identificacion_display',
        read_only=True
    )
    tipo_contribuyente_display = serializers.CharField(
        source='get_tipo_contribuyente_display',
        read_only=True
    )

    class Meta:
        model = Proveedor
        fields = [
            'id', 'uuid', 'nombre',
            'tipo_identificacion', 'tipo_identificacion_display',
            'numero_identificacion',
            'tipo_contribuyente', 'tipo_contribuyente_display',
            'telefono', 'correo_electronico',
            'es_internacional', 'activo',
            'fecha_creacion'
        ]
        read_only_fields = fields
