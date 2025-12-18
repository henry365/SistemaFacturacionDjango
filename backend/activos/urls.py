"""
URLs para Activos Fijos
"""
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import TipoActivoViewSet, ActivoFijoViewSet, DepreciacionViewSet

router = DefaultRouter()
router.register(r'tipos', TipoActivoViewSet)
router.register(r'activos', ActivoFijoViewSet)
router.register(r'depreciaciones', DepreciacionViewSet)

urlpatterns = [
    path('', include(router.urls)),
]
