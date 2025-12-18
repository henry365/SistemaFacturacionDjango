from django.core.management.base import BaseCommand
from django.contrib.auth.models import Group, Permission
from django.contrib.contenttypes.models import ContentType
from usuarios.models import User

class Command(BaseCommand):
    help = 'Configura los roles (Grupos) y permisos iniciales del sistema'

    def handle(self, *args, **options):
        self.stdout.write('Configurando roles y permisos...')

        # Definición de Roles y sus permisos asociados
        # Formato: 'rol': {'app': ['accion_modelo', ...]}
        roles_permissions = {
            'admin': '__all__', # Admin tiene todo
            
            'facturador': {
                'clientes': ['view_cliente', 'add_cliente', 'change_cliente'],
                'productos': ['view_producto', 'view_categoria'],
                'ventas': ['add_factura', 'view_factura', 'add_cotizacioncliente', 'view_cotizacioncliente', 'change_cotizacioncliente', 'add_detallefactura', 'add_detallecotizacion'],
                'vendedores': ['view_vendedor'],
            },
            
            'cajero': {
                'ventas': ['view_factura', 'add_pagocaja', 'view_pagocaja'],
                'clientes': ['view_cliente'],
            },
            
            'almacen': {
                'inventario': ['view_almacen', 'view_inventarioproducto', 'add_movimientoinventario', 'view_movimientoinventario'],
                'productos': ['view_producto', 'add_producto', 'change_producto', 'view_categoria'],
                'despachos': ['view_despacho', 'change_despacho'],
            },
            
            'compras': {
                'compras': ['add_solicitudcotizacionproveedor', 'view_solicitudcotizacionproveedor', 'change_solicitudcotizacionproveedor', 
                           'add_ordencompra', 'view_ordencompra', 'change_ordencompra',
                           'add_compra', 'view_compra'],
                'proveedores': ['view_proveedor', 'add_proveedor', 'change_proveedor'],
                'productos': ['view_producto', 'add_producto'],
            }
        }

        for role_name, apps_perms in roles_permissions.items():
            group, created = Group.objects.get_or_create(name=role_name)
            if created:
                self.stdout.write(f'Grupo creado: {role_name}')
            
            # Limpiar permisos anteriores para reiniciar configuración
            group.permissions.clear()

            if apps_perms == '__all__':
                # Si es admin, le damos todos los permisos existentes
                all_perms = Permission.objects.all()
                group.permissions.set(all_perms)
                self.stdout.write(f'  - Asignados TODOS los permisos a {role_name}')
                continue

            for app_label, perms_list in apps_perms.items():
                for perm_codename in perms_list:
                    try:
                        # Buscar el permiso
                        perm = Permission.objects.get(codename=perm_codename, content_type__app_label=app_label)
                        group.permissions.add(perm)
                        self.stdout.write(f'  - Asignado {perm_codename} a {role_name}')
                    except Permission.DoesNotExist:
                        self.stdout.write(self.style.WARNING(f'  ! Permiso no encontrado: {perm_codename} en app {app_label}'))

        self.stdout.write(self.style.SUCCESS('Configuración de roles completada con éxito.'))
