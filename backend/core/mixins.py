"""
Mixins para ViewSets del Sistema de Facturación.

Este módulo contiene mixins reutilizables para ViewSets de DRF:
- EmpresaFilterMixin: Filtrado automático por empresa del usuario
- EmpresaAuditMixin: Asignación automática de campos de auditoría

Ver también:
- core/filters.py: Mixins de filtrado por query params
- core/models/mixins.py: Mixins de validación para modelos
"""


class EmpresaFilterMixin:
    """
    Mixin para filtrar automáticamente por empresa del usuario en ViewSets.
    Requiere que el modelo tenga un campo 'empresa' ForeignKey.
    """
    def get_queryset(self):
        """Filtrar queryset según empresa del usuario"""
        queryset = super().get_queryset()
        user = self.request.user
        if user.is_authenticated and hasattr(user, 'empresa') and user.empresa:
            queryset = queryset.filter(empresa=user.empresa)
        return queryset


class EmpresaAuditMixin:
    """
    Mixin para asignar automáticamente empresa y usuarios de auditoría en ViewSets.
    Requiere que el modelo tenga campos: empresa, usuario_creacion, usuario_modificacion.
    """
    def perform_create(self, serializer):
        """Asignar empresa y usuarios al crear"""
        user = self.request.user
        kwargs = {
            'usuario_creacion': user,
            'usuario_modificacion': user
        }
        if user.is_authenticated and hasattr(user, 'empresa') and user.empresa:
            kwargs['empresa'] = user.empresa
        serializer.save(**kwargs)
    
    def perform_update(self, serializer):
        """Actualizar usuario de modificación"""
        serializer.save(usuario_modificacion=self.request.user)


class IdempotencyMixin:
    """
    Mixin para manejar idempotencia en operaciones de creación.

    Requiere que el modelo tenga un campo 'idempotency_key'.
    Busca la llave en el body (data) o en el header 'X-Idempotency-Key'.

    Comportamiento:
    - Si ya existe un registro con la misma idempotency_key, retorna el existente con HTTP 200
    - Si no existe, crea el nuevo registro con HTTP 201
    """
    def create(self, request, *args, **kwargs):
        from rest_framework.response import Response
        from rest_framework import status

        # Intentar obtener la llave del body o del header
        idempotency_key = request.data.get('idempotency_key') or request.headers.get('X-Idempotency-Key')

        if idempotency_key:
            # Verificar si ya existe un registro con esta llave
            existing = self.get_queryset().filter(idempotency_key=idempotency_key).first()

            if existing:
                # Si existe, retornamos el existente con código 200 (OK)
                serializer = self.get_serializer(existing)
                return Response(serializer.data, status=status.HTTP_200_OK)

            # Si no existe, asegurar que la llave esté en los datos
            if 'idempotency_key' not in request.data:
                if hasattr(request.data, '_mutable'):
                    request.data._mutable = True
                    request.data['idempotency_key'] = idempotency_key
                    request.data._mutable = False
                elif isinstance(request.data, dict):
                    request.data['idempotency_key'] = idempotency_key

        return super().create(request, *args, **kwargs)


class ProveedorEmpresaValidatorMixin:
    """
    Mixin para validar que proveedor pertenezca a la empresa en serializers.

    Requiere que el serializer tenga campos 'proveedor' y 'empresa'.
    Se usa principalmente en serializers del módulo compras.
    """
    def validate_proveedor_empresa(self, proveedor, empresa):
        """Valida que proveedor pertenezca a la misma empresa"""
        from rest_framework import serializers
        if proveedor and empresa and proveedor.empresa != empresa:
            raise serializers.ValidationError({
                "proveedor": "El proveedor debe pertenecer a la misma empresa."
            })

    def validate(self, data):
        """Validación completa que incluye proveedor-empresa"""
        proveedor = data.get('proveedor') or (self.instance.proveedor if self.instance else None)
        empresa = data.get('empresa') or (self.instance.empresa if self.instance else None)

        if proveedor and empresa:
            self.validate_proveedor_empresa(proveedor, empresa)

        return super().validate(data) if hasattr(super(), 'validate') else data
