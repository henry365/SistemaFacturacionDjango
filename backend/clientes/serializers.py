"""
Serializers para el módulo de Clientes

Este módulo contiene los serializers para Cliente y CategoriaCliente,
siguiendo los estándares de la Guía Inicial.
"""
from rest_framework import serializers
from django.core.validators import validate_email
from django.core.exceptions import ValidationError as DjangoValidationError

from .models import Cliente, CategoriaCliente
from .constants import TIPO_IDENTIFICACION_CHOICES, TIPOS_REQUIEREN_NUMERO


# ============================================================
# SERIALIZERS DE CATEGORIA CLIENTE
# ============================================================

class CategoriaClienteSerializer(serializers.ModelSerializer):
    """Serializer completo para CategoriaCliente"""
    empresa_nombre = serializers.ReadOnlyField(source='empresa.nombre')
    usuario_creacion_nombre = serializers.CharField(
        source='usuario_creacion.username', read_only=True
    )
    usuario_modificacion_nombre = serializers.CharField(
        source='usuario_modificacion.username', read_only=True
    )
    clientes_count = serializers.SerializerMethodField()

    class Meta:
        model = CategoriaCliente
        fields = [
            'id', 'uuid', 'nombre', 'descripcion',
            'descuento_porcentaje', 'activa',
            'fecha_creacion', 'fecha_actualizacion',
            'empresa', 'empresa_nombre',
            'usuario_creacion', 'usuario_creacion_nombre',
            'usuario_modificacion', 'usuario_modificacion_nombre',
            'clientes_count'
        ]
        read_only_fields = (
            'id', 'uuid', 'fecha_creacion', 'fecha_actualizacion',
            'usuario_creacion', 'usuario_modificacion', 'empresa'
        )

    def get_clientes_count(self, obj):
        """Retorna el número de clientes en esta categoría"""
        return obj.clientes.count()

    def validate_nombre(self, value):
        """Validar nombre no vacío"""
        if not value or not value.strip():
            raise serializers.ValidationError('El nombre no puede estar vacío.')
        return value.strip()

    def validate_descuento_porcentaje(self, value):
        """Validar descuento en rango válido"""
        if value is not None:
            if value < 0 or value > 100:
                raise serializers.ValidationError(
                    'El descuento debe estar entre 0 y 100.'
                )
        return value


class CategoriaClienteListSerializer(serializers.ModelSerializer):
    """Serializer simplificado para listados de CategoriaCliente"""
    clientes_count = serializers.SerializerMethodField()

    class Meta:
        model = CategoriaCliente
        fields = [
            'id', 'uuid', 'nombre', 'descripcion',
            'descuento_porcentaje', 'activa',
            'fecha_creacion', 'clientes_count'
        ]

    def get_clientes_count(self, obj):
        return obj.clientes.count()


# ============================================================
# SERIALIZERS DE CLIENTE
# ============================================================

class ClienteSerializer(serializers.ModelSerializer):
    """Serializer completo para Cliente"""
    categoria_nombre = serializers.ReadOnlyField(source='categoria.nombre')
    categoria_detalle = CategoriaClienteListSerializer(source='categoria', read_only=True)
    vendedor_nombre = serializers.ReadOnlyField(source='vendedor_asignado.nombre')
    vendedor_id = serializers.ReadOnlyField(source='vendedor_asignado.id')
    empresa_nombre = serializers.ReadOnlyField(source='empresa.nombre')
    usuario_creacion_nombre = serializers.CharField(
        source='usuario_creacion.username', read_only=True
    )
    usuario_modificacion_nombre = serializers.CharField(
        source='usuario_modificacion.username', read_only=True
    )
    tipo_identificacion_display = serializers.CharField(
        source='get_tipo_identificacion_display', read_only=True
    )
    # Hacer estos campos opcionales explícitamente
    numero_identificacion = serializers.CharField(
        max_length=50, required=False, allow_blank=True, allow_null=True
    )
    tipo_identificacion = serializers.ChoiceField(
        choices=TIPO_IDENTIFICACION_CHOICES,
        required=False, allow_blank=True, allow_null=True
    )

    class Meta:
        model = Cliente
        fields = [
            'id', 'uuid', 'nombre',
            'tipo_identificacion', 'tipo_identificacion_display',
            'numero_identificacion',
            'telefono', 'correo_electronico', 'direccion',
            'limite_credito', 'activo',
            'categoria', 'categoria_nombre', 'categoria_detalle',
            'vendedor_asignado', 'vendedor_id', 'vendedor_nombre',
            'empresa', 'empresa_nombre',
            'fecha_creacion', 'fecha_actualizacion',
            'usuario_creacion', 'usuario_creacion_nombre',
            'usuario_modificacion', 'usuario_modificacion_nombre'
        ]
        read_only_fields = (
            'id', 'uuid', 'fecha_creacion', 'fecha_actualizacion',
            'usuario_creacion', 'usuario_modificacion', 'empresa'
        )

    def validate_nombre(self, value):
        """Validar nombre no vacío"""
        if not value or not value.strip():
            raise serializers.ValidationError('El nombre no puede estar vacío.')
        return value.strip()

    def validate_correo_electronico(self, value):
        """Validar formato de correo electrónico"""
        if value:
            value = value.strip().lower()
            try:
                validate_email(value)
            except DjangoValidationError:
                raise serializers.ValidationError("Formato de correo electrónico inválido.")
        return value

    def validate_limite_credito(self, value):
        """Validar que el límite de crédito no sea negativo"""
        if value is not None and value < 0:
            raise serializers.ValidationError("El límite de crédito no puede ser negativo.")
        return value

    def validate_categoria(self, value):
        """
        Valida que la categoría pertenezca a la empresa del usuario.

        CRÍTICO: Siempre validar empresa en relaciones.
        """
        request = self.context.get('request')
        if request and hasattr(request.user, 'empresa'):
            user_empresa = request.user.empresa
            if value and value.empresa is not None and user_empresa is not None:
                if value.empresa != user_empresa:
                    raise serializers.ValidationError(
                        'La categoría debe pertenecer a su empresa.'
                    )
        return value

    def validate_vendedor_asignado(self, value):
        """
        Valida que el vendedor pertenezca a la empresa del usuario.

        CRÍTICO: Siempre validar empresa en relaciones.
        """
        request = self.context.get('request')
        if request and hasattr(request.user, 'empresa'):
            user_empresa = request.user.empresa
            if value and value.empresa is not None and user_empresa is not None:
                if value.empresa != user_empresa:
                    raise serializers.ValidationError(
                        'El vendedor debe pertenecer a su empresa.'
                    )
        return value

    def validate(self, data):
        """Validaciones de negocio personalizadas"""
        # Validar que tipos específicos requieren número de identificación
        tipo_identificacion = data.get('tipo_identificacion')
        numero_identificacion = data.get('numero_identificacion')

        if tipo_identificacion in TIPOS_REQUIEREN_NUMERO:
            if not numero_identificacion:
                raise serializers.ValidationError({
                    "numero_identificacion": f"El número de identificación es obligatorio para {tipo_identificacion}."
                })

        # Validar número de identificación único por empresa
        if numero_identificacion:
            request = self.context.get('request')
            empresa = None
            if request and hasattr(request.user, 'empresa'):
                empresa = request.user.empresa
            elif self.instance:
                empresa = self.instance.empresa

            if empresa:
                queryset = Cliente.objects.filter(
                    empresa=empresa,
                    numero_identificacion=numero_identificacion
                )
                if self.instance:
                    queryset = queryset.exclude(pk=self.instance.pk)
                if queryset.exists():
                    raise serializers.ValidationError({
                        "numero_identificacion": f"Ya existe un cliente con este número de identificación."
                    })

        return data


class ClienteListSerializer(serializers.ModelSerializer):
    """Serializer simplificado para listados de Cliente"""
    categoria_nombre = serializers.ReadOnlyField(source='categoria.nombre')
    vendedor_nombre = serializers.ReadOnlyField(source='vendedor_asignado.nombre')
    tipo_identificacion_display = serializers.CharField(
        source='get_tipo_identificacion_display', read_only=True
    )

    class Meta:
        model = Cliente
        fields = [
            'id', 'uuid', 'nombre',
            'tipo_identificacion', 'tipo_identificacion_display',
            'numero_identificacion',
            'telefono', 'correo_electronico',
            'limite_credito', 'activo',
            'categoria', 'categoria_nombre',
            'vendedor_asignado', 'vendedor_nombre',
            'fecha_creacion'
        ]


class ClienteResumenSerializer(serializers.Serializer):
    """Serializer para el resumen de cliente"""
    cliente_id = serializers.IntegerField()
    cliente_nombre = serializers.CharField()
    total_facturas = serializers.IntegerField()
    total_ventas = serializers.DecimalField(max_digits=14, decimal_places=2)
    total_pendiente = serializers.DecimalField(max_digits=14, decimal_places=2)
    total_pagos = serializers.IntegerField()
    total_pagado = serializers.DecimalField(max_digits=14, decimal_places=2)
    saldo_actual = serializers.DecimalField(max_digits=14, decimal_places=2)
    limite_credito = serializers.DecimalField(max_digits=14, decimal_places=2)
    credito_disponible = serializers.DecimalField(
        max_digits=14, decimal_places=2, allow_null=True
    )
