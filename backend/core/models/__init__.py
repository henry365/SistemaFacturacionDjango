"""
Modelos del módulo Core.

Este paquete contiene:
- Modelos abstractos base (DRY)
- Mixins de validación reutilizables
- Modelo de configuración por empresa
"""

# Modelos abstractos base
from .base import (
    AbstractBaseModel,
    AbstractAuditModel,
    AbstractMultitenantModel,
    AbstractDocumentoModel,
    AbstractDetalleModel,
)

# Mixins de validación
from .mixins import (
    ValidateMultitenantMixin,
    ValidateMoneyFieldsMixin,
    ValidateQuantityMixin,
    ValidateDateRangeMixin,
    DisplayChoicesMixin,
    ActualizarEstadoMixin,
)

# Modelo de configuración
from .configuracion import (
    ConfiguracionEmpresa,
    CONFIG_SECTIONS,
    crear_configuracion_empresa,
)

__all__ = [
    # Base models
    'AbstractBaseModel',
    'AbstractAuditModel',
    'AbstractMultitenantModel',
    'AbstractDocumentoModel',
    'AbstractDetalleModel',
    # Mixins
    'ValidateMultitenantMixin',
    'ValidateMoneyFieldsMixin',
    'ValidateQuantityMixin',
    'ValidateDateRangeMixin',
    'DisplayChoicesMixin',
    'ActualizarEstadoMixin',
    # Configuration
    'ConfiguracionEmpresa',
    'CONFIG_SECTIONS',
    'crear_configuracion_empresa',
]
