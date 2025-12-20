"""
Migración para agregar permisos personalizados a los modelos de ventas.
"""
from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('ventas', '0004_alter_detallefactura_importe'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='cotizacioncliente',
            options={
                'ordering': ['-fecha'],
                'permissions': [('gestionar_cotizacion', 'Puede gestionar cotizaciones')],
                'verbose_name': 'Cotización',
                'verbose_name_plural': 'Cotizaciones',
            },
        ),
        migrations.AlterModelOptions(
            name='factura',
            options={
                'ordering': ['-fecha'],
                'permissions': [('gestionar_factura', 'Puede gestionar facturas')],
                'verbose_name': 'Factura',
                'verbose_name_plural': 'Facturas',
            },
        ),
        migrations.AlterModelOptions(
            name='pagocaja',
            options={
                'ordering': ['-fecha_pago'],
                'permissions': [('gestionar_pago_caja', 'Puede gestionar pagos en caja')],
                'verbose_name': 'Pago en Caja',
                'verbose_name_plural': 'Pagos en Caja',
            },
        ),
        migrations.AlterModelOptions(
            name='notacredito',
            options={
                'ordering': ['-fecha'],
                'permissions': [('gestionar_nota_credito', 'Puede gestionar notas de crédito')],
                'verbose_name': 'Nota de Crédito',
                'verbose_name_plural': 'Notas de Crédito',
            },
        ),
        migrations.AlterModelOptions(
            name='notadebito',
            options={
                'ordering': ['-fecha'],
                'permissions': [('gestionar_nota_debito', 'Puede gestionar notas de débito')],
                'verbose_name': 'Nota de Débito',
                'verbose_name_plural': 'Notas de Débito',
            },
        ),
        migrations.AlterModelOptions(
            name='devolucionventa',
            options={
                'ordering': ['-fecha'],
                'permissions': [('gestionar_devolucion_venta', 'Puede gestionar devoluciones de venta')],
                'verbose_name': 'Devolución de Venta',
                'verbose_name_plural': 'Devoluciones de Venta',
            },
        ),
        migrations.AlterModelOptions(
            name='listaesperaproducto',
            options={
                'ordering': ['-fecha_solicitud', 'prioridad'],
                'permissions': [('gestionar_lista_espera', 'Puede gestionar listas de espera')],
                'verbose_name': 'Lista de Espera',
                'verbose_name_plural': 'Listas de Espera',
            },
        ),
    ]
