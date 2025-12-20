"""
Serializers para el módulo Vendedores

Este módulo contiene los serializers para gestión de vendedores
con validaciones de negocio.
"""
from rest_framework import serializers
from django.core.validators import validate_email
from django.core.exceptions import ValidationError as DjangoValidationError
from django.db.models import Sum
import re

from .models import Vendedor
from .constants import (
    ERROR_TELEFONO_INVALIDO,
    ERROR_TELEFONO_LONGITUD,
    ERROR_EMAIL_INVALIDO,
    ERROR_COMISION_RANGO,
    ERROR_CEDULA_DUPLICADA,
    REGEX_TELEFONO,
    COMISION_MIN,
    COMISION_MAX,
)


class VendedorSerializer(serializers.ModelSerializer):
    """
    Serializer completo para Vendedor.

    Incluye todos los campos y validaciones para crear/actualizar.
    """
    empresa_nombre = serializers.ReadOnlyField(source='empresa.nombre')
    usuario_username = serializers.ReadOnlyField(source='usuario.username')
    total_clientes = serializers.SerializerMethodField()
    total_ventas = serializers.SerializerMethodField()

    class Meta:
        model = Vendedor
        fields = [
            'id', 'uuid', 'empresa', 'empresa_nombre',
            'nombre', 'cedula', 'telefono', 'correo',
            'comision_porcentaje', 'usuario', 'usuario_username',
            'activo', 'fecha_creacion', 'fecha_actualizacion',
            'usuario_creacion', 'usuario_modificacion',
            'idempotency_key', 'total_clientes', 'total_ventas'
        ]
        read_only_fields = [
            'id', 'uuid', 'empresa', 'fecha_creacion', 'fecha_actualizacion',
            'usuario_creacion', 'usuario_modificacion'
        ]

    def get_total_clientes(self, obj):
        """Contar clientes asignados al vendedor"""
        return obj.clientes.count()

    def get_total_ventas(self, obj):
        """Calcular total de ventas del vendedor"""
        from ventas.models import Factura
        ventas = Factura.objects.filter(vendedor=obj)
        total = ventas.aggregate(total=Sum('total'))['total'] or 0
        return float(total)

    def validate_correo(self, value):
        """Validar formato de correo electrónico"""
        if value:
            try:
                validate_email(value)
            except DjangoValidationError:
                raise serializers.ValidationError(ERROR_EMAIL_INVALIDO)
        return value

    def validate_telefono(self, value):
        """Validar formato de teléfono"""
        if value:
            if not re.match(REGEX_TELEFONO, value):
                raise serializers.ValidationError(ERROR_TELEFONO_INVALIDO)
            telefono_sin_formato = re.sub(r'[\s\-\(\)]', '', value)
            if len(telefono_sin_formato) < 10 or len(telefono_sin_formato) > 15:
                raise serializers.ValidationError(ERROR_TELEFONO_LONGITUD)
        return value

    def validate_comision_porcentaje(self, value):
        """Validar que la comisión esté entre 0 y 100"""
        if value < COMISION_MIN or value > COMISION_MAX:
            raise serializers.ValidationError(ERROR_COMISION_RANGO)
        return value

    def validate(self, data):
        """Validaciones de negocio personalizadas"""
        # Validar cédula única por empresa
        cedula = data.get('cedula')
        if cedula:
            # Obtener empresa del contexto o de la instancia
            request = self.context.get('request')
            empresa = None
            if request and hasattr(request.user, 'empresa'):
                empresa = request.user.empresa
            elif self.instance:
                empresa = self.instance.empresa

            if empresa:
                queryset = Vendedor.objects.filter(empresa=empresa, cedula=cedula)
                if self.instance:
                    queryset = queryset.exclude(pk=self.instance.pk)
                if queryset.exists():
                    raise serializers.ValidationError({
                        "cedula": ERROR_CEDULA_DUPLICADA.format(empresa=empresa.nombre)
                    })
        return data


class VendedorListSerializer(serializers.ModelSerializer):
    """
    Serializer optimizado para listado de Vendedores.

    Incluye solo campos esenciales para mejorar rendimiento en listados.
    """
    empresa_nombre = serializers.ReadOnlyField(source='empresa.nombre')
    usuario_username = serializers.ReadOnlyField(source='usuario.username')

    class Meta:
        model = Vendedor
        fields = [
            'id', 'uuid', 'nombre', 'cedula',
            'telefono', 'correo', 'comision_porcentaje',
            'usuario', 'usuario_username', 'activo',
            'empresa_nombre', 'fecha_creacion'
        ]
        read_only_fields = fields
