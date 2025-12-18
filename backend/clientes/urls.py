from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import ClienteViewSet, CategoriaClienteViewSet

router = DefaultRouter()
router.register(r'clientes', ClienteViewSet)
router.register(r'categorias-clientes', CategoriaClienteViewSet)

urlpatterns = [
    path('', include(router.urls)),
]
