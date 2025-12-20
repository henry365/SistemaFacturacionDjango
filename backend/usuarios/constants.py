"""
Constantes para el módulo de Usuarios
"""

# Roles de usuario
ROL_ADMIN = 'admin'
ROL_FACTURADOR = 'facturador'
ROL_CAJERO = 'cajero'
ROL_ALMACEN = 'almacen'
ROL_COMPRAS = 'compras'
ROL_CONTABILIDAD = 'contabilidad'

ROL_CHOICES = (
    (ROL_ADMIN, 'Administrador'),
    (ROL_FACTURADOR, 'Facturador'),
    (ROL_CAJERO, 'Cajero'),
    (ROL_ALMACEN, 'Almacén'),
    (ROL_COMPRAS, 'Compras'),
    (ROL_CONTABILIDAD, 'Contabilidad'),
)

ROLES_VALIDOS = [r[0] for r in ROL_CHOICES]

# Rol por defecto para nuevos usuarios
ROL_DEFAULT = ROL_FACTURADOR
