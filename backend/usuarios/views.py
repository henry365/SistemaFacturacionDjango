from rest_framework import status, viewsets, permissions, filters
from rest_framework.decorators import api_view, permission_classes, action
from rest_framework.permissions import AllowAny, IsAdminUser
from rest_framework.response import Response
from rest_framework_simplejwt.views import TokenObtainPairView
from django.contrib.auth.models import Group, Permission
from django.contrib.auth import get_user_model
from empresas.models import Empresa
from .serializers import (
    CustomTokenObtainPairSerializer, EmpresaLoginSerializer,
    UserSerializer, UserCreateSerializer, UserUpdateSerializer,
    ChangePasswordSerializer, GroupSerializer, PermissionSerializer
)
from .permissions import ActionBasedPermission, IsAdminOrSameEmpresa, IsOwnerOrReadOnly, require_permission
from core.mixins import IdempotencyMixin

User = get_user_model()

class CustomTokenObtainPairView(TokenObtainPairView):
    """
    Vista personalizada para obtener token JWT.
    
    Requiere:
    - empresa_username: Nombre de la empresa
    - username: Nombre de usuario
    - password: Contraseña
    
    El usuario debe pertenecer a la empresa especificada.
    """
    serializer_class = CustomTokenObtainPairSerializer

@api_view(['POST'])
@permission_classes([AllowAny])
def validar_empresa(request):
    """
    Endpoint para validar que una empresa existe antes del login.
    Útil para mostrar mensajes de error específicos en el frontend.
    """
    serializer = EmpresaLoginSerializer(data=request.data)
    
    if serializer.is_valid():
        empresa_username = serializer.validated_data['empresa_username']
        empresa = Empresa.objects.get(nombre=empresa_username, activo=True)
        
        return Response({
            'valida': True,
            'empresa': {
                'id': empresa.id,
                'nombre': empresa.nombre,
                'rnc': empresa.rnc
            }
        })
    
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class UserViewSet(IdempotencyMixin, viewsets.ModelViewSet):
    """
    ViewSet para gestionar usuarios.
    
    Los usuarios normales solo pueden ver/editar su propio perfil.
    Los administradores pueden gestionar todos los usuarios de su empresa.
    """
    queryset = User.objects.all()
    permission_classes = [permissions.IsAuthenticated, ActionBasedPermission, IsAdminOrSameEmpresa]
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['username', 'email', 'first_name', 'last_name']
    ordering_fields = ['username', 'date_joined', 'rol', 'is_active']
    ordering = ['username']
    
    def get_serializer_class(self):
        """Usar serializer apropiado según la acción"""
        if self.action == 'create':
            return UserCreateSerializer
        elif self.action in ['update', 'partial_update']:
            return UserUpdateSerializer
        return UserSerializer
    
    def get_queryset(self):
        """Filtrar usuarios según empresa y permisos"""
        user = self.request.user
        queryset = super().get_queryset()
        
        # Administradores ven todos los usuarios de su empresa
        if user.is_staff or user.is_superuser:
            if hasattr(user, 'empresa') and user.empresa:
                queryset = queryset.filter(empresa=user.empresa)
        else:
            # Usuarios normales solo ven su propio usuario
            queryset = queryset.filter(id=user.id)
        
        # Filtros específicos
        activo = self.request.query_params.get('activo')
        if activo is not None:
            queryset = queryset.filter(is_active=activo.lower() == 'true')
        
        rol = self.request.query_params.get('rol')
        if rol:
            queryset = queryset.filter(rol=rol)
        
        empresa_id = self.request.query_params.get('empresa')
        if empresa_id and (user.is_staff or user.is_superuser):
            queryset = queryset.filter(empresa_id=empresa_id)
        
        return queryset
    
    def get_permissions(self):
        """Permisos específicos por acción"""
        if self.action in ['perfil', 'actualizar_perfil', 'cambiar_password']:
            # Acciones de perfil propio solo requieren autenticación
            return [permissions.IsAuthenticated()]
        elif self.action in ['create', 'update', 'partial_update', 'destroy']:
            # CRUD requiere permisos de admin o mismo usuario
            return [permissions.IsAuthenticated(), IsAdminOrSameEmpresa()]
        return super().get_permissions()
    
    def perform_create(self, serializer):
        """Asignar empresa al crear usuario"""
        user = self.request.user
        if hasattr(user, 'empresa') and user.empresa:
            serializer.save(empresa=user.empresa)
        else:
            serializer.save()
    
    @action(detail=False, methods=['get'])
    def perfil(self, request):
        """Obtener perfil del usuario autenticado"""
        serializer = self.get_serializer(request.user)
        return Response(serializer.data)
    
    @action(detail=False, methods=['patch', 'put'])
    def actualizar_perfil(self, request):
        """Actualizar perfil del usuario autenticado"""
        serializer = UserUpdateSerializer(request.user, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    @action(detail=False, methods=['post'])
    def cambiar_password(self, request):
        """Cambiar contraseña del usuario autenticado"""
        serializer = ChangePasswordSerializer(data=request.data, context={'request': request})
        if serializer.is_valid():
            user = request.user
            user.set_password(serializer.validated_data['password_nuevo'])
            user.save()
            return Response({'mensaje': 'Contraseña actualizada correctamente'})
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    @action(detail=True, methods=['post'])
    @require_permission('usuarios.change_user')
    def activar(self, request, pk=None):
        """Activar usuario (solo admin)"""
        usuario = self.get_object()
        usuario.is_active = True
        usuario.save()
        return Response({'mensaje': f'Usuario {usuario.username} activado correctamente'})
    
    @action(detail=True, methods=['post'])
    @require_permission('usuarios.change_user')
    def desactivar(self, request, pk=None):
        """Desactivar usuario (solo admin)"""
        usuario = self.get_object()
        usuario.is_active = False
        usuario.save()
        return Response({'mensaje': f'Usuario {usuario.username} desactivado correctamente'})
    
    @action(detail=True, methods=['post'])
    @require_permission('usuarios.change_user')
    def asignar_permisos(self, request, pk=None):
        """Asignar permisos a un usuario (solo admin)"""
        usuario = self.get_object()
        permisos_ids = request.data.get('permisos', [])
        
        try:
            permisos = Permission.objects.filter(id__in=permisos_ids)
            usuario.user_permissions.add(*permisos)
            return Response({
                'mensaje': f'Permisos asignados correctamente a {usuario.username}',
                'permisos_asignados': permisos.count()
            })
        except Exception as e:
            return Response(
                {'error': str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )
    
    @action(detail=True, methods=['post'])
    @require_permission('usuarios.change_user')
    def quitar_permisos(self, request, pk=None):
        """Quitar permisos de un usuario (solo admin)"""
        usuario = self.get_object()
        permisos_ids = request.data.get('permisos', [])
        
        try:
            permisos = Permission.objects.filter(id__in=permisos_ids)
            usuario.user_permissions.remove(*permisos)
            return Response({
                'mensaje': f'Permisos quitados correctamente de {usuario.username}',
                'permisos_quitados': permisos.count()
            })
        except Exception as e:
            return Response(
                {'error': str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )
    
    @action(detail=True, methods=['post'])
    @require_permission('usuarios.change_user')
    def asignar_grupo(self, request, pk=None):
        """Asignar grupo/rol a un usuario (solo admin)"""
        usuario = self.get_object()
        grupo_id = request.data.get('grupo_id')
        grupo_nombre = request.data.get('grupo_nombre')
        
        try:
            if grupo_id:
                grupo = Group.objects.get(id=grupo_id)
            elif grupo_nombre:
                grupo = Group.objects.get(name=grupo_nombre)
            else:
                return Response(
                    {'error': 'Se requiere grupo_id o grupo_nombre'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            usuario.groups.add(grupo)
            return Response({
                'mensaje': f'Grupo {grupo.name} asignado correctamente a {usuario.username}'
            })
        except Group.DoesNotExist:
            return Response(
                {'error': 'Grupo no encontrado'},
                status=status.HTTP_404_NOT_FOUND
            )
        except Exception as e:
            return Response(
                {'error': str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )
    
    @action(detail=True, methods=['post'])
    @require_permission('usuarios.change_user')
    def quitar_grupo(self, request, pk=None):
        """Quitar grupo/rol de un usuario (solo admin)"""
        usuario = self.get_object()
        grupo_id = request.data.get('grupo_id')
        grupo_nombre = request.data.get('grupo_nombre')
        
        try:
            if grupo_id:
                grupo = Group.objects.get(id=grupo_id)
            elif grupo_nombre:
                grupo = Group.objects.get(name=grupo_nombre)
            else:
                return Response(
                    {'error': 'Se requiere grupo_id o grupo_nombre'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            usuario.groups.remove(grupo)
            return Response({
                'mensaje': f'Grupo {grupo.name} quitado correctamente de {usuario.username}'
            })
        except Group.DoesNotExist:
            return Response(
                {'error': 'Grupo no encontrado'},
                status=status.HTTP_404_NOT_FOUND
            )
        except Exception as e:
            return Response(
                {'error': str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )

class GroupViewSet(viewsets.ModelViewSet):
    """
    ViewSet para gestionar grupos/roles.
    Solo accesible para administradores.
    """
    queryset = Group.objects.all()
    serializer_class = GroupSerializer
    permission_classes = [IsAdminUser]
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['name']
    ordering_fields = ['name']
    ordering = ['name']
    
    @action(detail=True, methods=['get'])
    def permisos(self, request, pk=None):
        """Listar permisos del grupo"""
        grupo = self.get_object()
        permisos = grupo.permissions.all()
        serializer = PermissionSerializer(permisos, many=True)
        return Response(serializer.data)
    
    @action(detail=True, methods=['post'])
    def asignar_permisos(self, request, pk=None):
        """Asignar permisos al grupo"""
        grupo = self.get_object()
        permisos_ids = request.data.get('permisos', [])
        
        try:
            permisos = Permission.objects.filter(id__in=permisos_ids)
            grupo.permissions.add(*permisos)
            return Response({
                'mensaje': f'Permisos asignados correctamente al grupo {grupo.name}',
                'permisos_asignados': permisos.count()
            })
        except Exception as e:
            return Response(
                {'error': str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )
    
    @action(detail=True, methods=['post'])
    def quitar_permisos(self, request, pk=None):
        """Quitar permisos del grupo"""
        grupo = self.get_object()
        permisos_ids = request.data.get('permisos', [])
        
        try:
            permisos = Permission.objects.filter(id__in=permisos_ids)
            grupo.permissions.remove(*permisos)
            return Response({
                'mensaje': f'Permisos quitados correctamente del grupo {grupo.name}',
                'permisos_quitados': permisos.count()
            })
        except Exception as e:
            return Response(
                {'error': str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )
    
    @action(detail=True, methods=['get'])
    def usuarios(self, request, pk=None):
        """Listar usuarios del grupo"""
        grupo = self.get_object()
        usuarios = grupo.user_set.all()
        serializer = UserSerializer(usuarios, many=True)
        return Response({
            'grupo': grupo.name,
            'total_usuarios': usuarios.count(),
            'usuarios': serializer.data
        })

class PermissionViewSet(viewsets.ReadOnlyModelViewSet):
    """
    ViewSet para listar permisos disponibles (solo lectura).
    Solo accesible para administradores.
    """
    queryset = Permission.objects.all()
    serializer_class = PermissionSerializer
    permission_classes = [IsAdminUser]
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['name', 'codename', 'content_type__app_label', 'content_type__model']
    ordering_fields = ['content_type__app_label', 'content_type__model', 'codename']
    ordering = ['content_type__app_label', 'content_type__model', 'codename']
    
    def get_queryset(self):
        """Filtrar permisos por app_label si se proporciona"""
        queryset = super().get_queryset()
        app_label = self.request.query_params.get('app_label')
        if app_label:
            queryset = queryset.filter(content_type__app_label=app_label)
        return queryset
