"""
Views para el módulo de Configuración del Sistema.

Este módulo expone la API REST para gestionar la configuración
de empresa con permisos estrictos (solo administradores).
"""
from rest_framework import viewsets, status, permissions
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.shortcuts import get_object_or_404

from .models import ConfiguracionEmpresa
from .serializers import (
    ConfiguracionEmpresaSerializer,
    ConfiguracionEmpresaResumenSerializer,
    RestablecerSeccionSerializer,
    ActualizarSeccionSerializer,
)
from .config import get_config_defaults
from core.permissions.mixins import AdminStaffMixin


class IsAdminRole(AdminStaffMixin, permissions.BasePermission):
    """
    Permiso que verifica si el usuario tiene rol 'admin' o es staff/superuser.

    Usa AdminStaffMixin de core.permissions para la verificación de admin/staff.
    """

    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False

        # Superusers y staff siempre tienen acceso (usando mixin)
        if self._is_admin_or_staff(request.user):
            return True

        # Verificar rol 'admin'
        return getattr(request.user, 'rol', None) == 'admin'


class ConfiguracionEmpresaViewSet(viewsets.ModelViewSet):
    """
    ViewSet para gestionar la configuración de empresa.

    Solo usuarios con rol 'admin' o staff/superuser pueden acceder.
    Cada usuario solo puede ver/editar la configuración de su propia empresa.

    Acciones disponibles:
    - GET /configuracion/ - Lista (solo ve su empresa)
    - GET /configuracion/{id}/ - Detalle
    - PATCH /configuracion/{id}/ - Actualizar parcialmente
    - GET /configuracion/mi_configuracion/ - Obtener config de la empresa actual
    - POST /configuracion/restablecer_seccion/ - Restablecer una sección
    - POST /configuracion/actualizar_seccion/ - Actualizar una sección específica
    - GET /configuracion/valores_defecto/ - Ver valores por defecto
    """
    queryset = ConfiguracionEmpresa.objects.select_related(
        'empresa', 'usuario_creacion', 'usuario_modificacion'
    )
    permission_classes = [IsAuthenticated, IsAdminRole]

    def get_serializer_class(self):
        if self.action == 'list':
            return ConfiguracionEmpresaResumenSerializer
        return ConfiguracionEmpresaSerializer

    def get_queryset(self):
        """
        Filtrar configuraciones solo de la empresa del usuario.
        Superusers pueden ver todas.
        """
        user = self.request.user
        queryset = super().get_queryset()

        if user.is_superuser:
            return queryset

        # Filtrar por empresa del usuario
        if hasattr(user, 'empresa') and user.empresa:
            return queryset.filter(empresa=user.empresa)

        return queryset.none()

    def create(self, request, *args, **kwargs):
        """
        No permitir crear configuraciones manualmente.
        Se crean automáticamente al crear una empresa.
        """
        return Response(
            {'error': 'Las configuraciones se crean automáticamente con cada empresa.'},
            status=status.HTTP_405_METHOD_NOT_ALLOWED
        )

    def destroy(self, request, *args, **kwargs):
        """
        No permitir eliminar configuraciones.
        """
        return Response(
            {'error': 'No se puede eliminar la configuración de una empresa.'},
            status=status.HTTP_405_METHOD_NOT_ALLOWED
        )

    def update(self, request, *args, **kwargs):
        """
        Solo permitir actualizaciones parciales (PATCH).
        """
        if request.method == 'PUT':
            return Response(
                {'error': 'Use PATCH para actualizaciones parciales.'},
                status=status.HTTP_405_METHOD_NOT_ALLOWED
            )
        return super().update(request, *args, **kwargs)

    @action(detail=False, methods=['get'])
    def mi_configuracion(self, request):
        """
        Obtener la configuración de la empresa del usuario actual.
        Si no existe, la crea con valores por defecto.
        """
        user = request.user

        if not hasattr(user, 'empresa') or not user.empresa:
            return Response(
                {'error': 'El usuario no tiene una empresa asignada.'},
                status=status.HTTP_400_BAD_REQUEST
            )

        config, created = ConfiguracionEmpresa.objects.get_or_create(
            empresa=user.empresa,
            defaults={
                'usuario_creacion': user,
            }
        )

        serializer = ConfiguracionEmpresaSerializer(
            config, context={'request': request}
        )
        return Response(serializer.data)

    @action(detail=False, methods=['post'])
    def restablecer_seccion(self, request):
        """
        Restablece una sección específica a sus valores por defecto.

        Body:
            seccion: "fiscal" | "facturacion" | "inventario" | "notificaciones" |
                     "reportes" | "compras" | "seguridad" | "todo"

        Notas:
        - Solo superusers pueden restablecer la sección fiscal
        - "todo" restablece todas las secciones
        """
        serializer = RestablecerSeccionSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        seccion = serializer.validated_data['seccion']
        user = request.user

        if not hasattr(user, 'empresa') or not user.empresa:
            return Response(
                {'error': 'El usuario no tiene una empresa asignada.'},
                status=status.HTTP_400_BAD_REQUEST
            )

        config = get_object_or_404(ConfiguracionEmpresa, empresa=user.empresa)

        # Verificar permisos para sección fiscal
        if seccion in ['fiscal', 'todo'] and not user.is_superuser:
            return Response(
                {'error': 'Solo superusers pueden restablecer la configuración fiscal.'},
                status=status.HTTP_403_FORBIDDEN
            )

        # Registrar usuario de modificación
        config.usuario_modificacion = user

        if seccion == 'todo':
            config.restablecer_todo()
            mensaje = 'Todas las secciones han sido restablecidas.'
        else:
            if config.restablecer_seccion(seccion):
                mensaje = f'La sección "{seccion}" ha sido restablecida.'
            else:
                return Response(
                    {'error': f'Sección "{seccion}" no válida.'},
                    status=status.HTTP_400_BAD_REQUEST
                )

        return Response({
            'message': mensaje,
            'configuracion': ConfiguracionEmpresaSerializer(
                config, context={'request': request}
            ).data
        })

    @action(detail=False, methods=['post'])
    def actualizar_seccion(self, request):
        """
        Actualiza valores específicos de una sección.

        Body:
            seccion: "fiscal" | "facturacion" | ... (ver serializer)
            valores: {clave: valor, ...}

        Notas:
        - Solo superusers pueden modificar la sección fiscal
        - Los valores se validan según la sección
        """
        serializer = ActualizarSeccionSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        seccion = serializer.validated_data['seccion']
        valores = serializer.validated_data['valores']
        user = request.user

        if not hasattr(user, 'empresa') or not user.empresa:
            return Response(
                {'error': 'El usuario no tiene una empresa asignada.'},
                status=status.HTTP_400_BAD_REQUEST
            )

        config = get_object_or_404(ConfiguracionEmpresa, empresa=user.empresa)

        # Verificar permisos para sección fiscal
        if seccion == 'fiscal' and not user.is_superuser:
            return Response(
                {'error': 'Solo superusers pueden modificar la configuración fiscal.'},
                status=status.HTTP_403_FORBIDDEN
            )

        # Mapeo de secciones a campos
        campos = {
            'fiscal': 'config_fiscal',
            'facturacion': 'config_facturacion',
            'inventario': 'config_inventario',
            'notificaciones': 'config_notificaciones',
            'reportes': 'config_reportes',
            'compras': 'config_compras',
            'seguridad': 'config_seguridad',
        }

        campo = campos.get(seccion)
        if not campo:
            return Response(
                {'error': f'Sección "{seccion}" no válida.'},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Obtener configuración actual y actualizar solo los valores proporcionados
        config_actual = getattr(config, campo)
        config_actual.update(valores)
        setattr(config, campo, config_actual)
        config.usuario_modificacion = user
        config.save(update_fields=[campo, 'usuario_modificacion', 'fecha_actualizacion'])

        return Response({
            'message': f'Sección "{seccion}" actualizada correctamente.',
            'seccion': seccion,
            'valores_actualizados': valores,
            'configuracion_seccion': config_actual
        })

    @action(detail=False, methods=['get'])
    def valores_defecto(self, request):
        """
        Retorna todos los valores de configuración por defecto.
        Útil para mostrar qué valores se usarán si no hay configuración personalizada.
        """
        # Solo superusers pueden ver valores fiscales por defecto
        defaults = get_config_defaults()

        if not request.user.is_superuser:
            # Ocultar algunos valores sensibles de fiscal
            defaults['fiscal'] = {
                k: v for k, v in defaults['fiscal'].items()
                if not k.startswith('RETENCION')
            }

        return Response(defaults)

    @action(detail=False, methods=['get'])
    def resumen(self, request):
        """
        Retorna un resumen de la configuración actual de la empresa.
        """
        user = request.user

        if not hasattr(user, 'empresa') or not user.empresa:
            return Response(
                {'error': 'El usuario no tiene una empresa asignada.'},
                status=status.HTTP_400_BAD_REQUEST
            )

        config = get_object_or_404(ConfiguracionEmpresa, empresa=user.empresa)

        # Crear resumen con valores clave
        resumen = {
            'empresa': config.empresa.nombre,
            'ultima_actualizacion': config.fecha_actualizacion,
            'facturacion': {
                'dias_credito': config.get_valor('facturacion', 'DIAS_CREDITO_DEFAULT'),
                'moneda': config.get_valor('facturacion', 'MONEDA_DEFAULT'),
                'descuento_maximo': config.get_valor('facturacion', 'DESCUENTO_MAXIMO_PORCENTAJE'),
            },
            'inventario': {
                'metodo_costeo': config.get_valor('inventario', 'METODO_COSTEO'),
                'stock_negativo': config.get_valor('inventario', 'PERMITIR_STOCK_NEGATIVO'),
                'alertas_activas': config.get_valor('inventario', 'HABILITAR_ALERTAS_STOCK'),
            },
            'notificaciones': {
                'email_facturas': config.get_valor('notificaciones', 'HABILITAR_EMAIL_FACTURA'),
                'email_cxc_vencida': config.get_valor('notificaciones', 'HABILITAR_EMAIL_CXC_VENCIDA'),
                'email_stock_bajo': config.get_valor('notificaciones', 'HABILITAR_EMAIL_STOCK_BAJO'),
            },
            'seguridad': {
                'tiempo_sesion_minutos': config.get_valor('seguridad', 'TIEMPO_SESION_MINUTOS'),
                'max_intentos_login': config.get_valor('seguridad', 'MAX_INTENTOS_LOGIN'),
            },
        }

        return Response(resumen)
