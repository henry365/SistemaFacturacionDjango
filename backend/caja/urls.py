from rest_framework.routers import DefaultRouter
from .views import CajaViewSet, SesionCajaViewSet, MovimientoCajaViewSet

router = DefaultRouter()
router.register(r'cajas', CajaViewSet)
router.register(r'sesiones', SesionCajaViewSet)
router.register(r'movimientos', MovimientoCajaViewSet)

urlpatterns = router.urls
