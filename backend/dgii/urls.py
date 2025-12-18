"""
URLs para DGII (Comprobantes Fiscales)
"""
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import TipoComprobanteViewSet, SecuenciaNCFViewSet

router = DefaultRouter()
router.register(r'tipos-comprobante', TipoComprobanteViewSet)
router.register(r'secuencias', SecuenciaNCFViewSet)

urlpatterns = [
    path('', include(router.urls)),
]
