"""
URLs para el módulo de Usuarios
"""
from django.urls import path, include
from rest_framework.routers import DefaultRouter

from .views import (
    CustomTokenObtainPairView,
    validar_empresa,
    UserViewSet,
    GroupViewSet,
    PermissionViewSet,
)

app_name = 'usuarios'

router = DefaultRouter()
router.register(r'usuarios', UserViewSet, basename='usuario')
router.register(r'grupos', GroupViewSet, basename='grupo')
router.register(r'permisos', PermissionViewSet, basename='permiso')

urlpatterns = [
    # Autenticación
    path('auth/token/', CustomTokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('auth/validar-empresa/', validar_empresa, name='validar_empresa'),

    # ViewSets
    path('', include(router.urls)),
]
