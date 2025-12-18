"""
URLs para Cuentas por Cobrar
"""
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import CuentaPorCobrarViewSet, CobroClienteViewSet, DetalleCobroClienteViewSet

router = DefaultRouter()
router.register(r'cuentas-por-cobrar', CuentaPorCobrarViewSet)
router.register(r'cobros-clientes', CobroClienteViewSet)
router.register(r'detalle-cobros-clientes', DetalleCobroClienteViewSet)

urlpatterns = [
    path('', include(router.urls)),
]
