"""
Migración para agregar permisos personalizados al modelo Vendedor.
"""
from django.db import migrations, models


class Migration(migrations.Migration):
    """Agrega Meta.permissions."""

    dependencies = [
        ('vendedores', '0003_alter_vendedor_activo_alter_vendedor_cedula_and_more'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='vendedor',
            options={
                'ordering': ['nombre'],
                'permissions': [('gestionar_vendedor', 'Puede gestionar vendedores')],
                'verbose_name': 'Vendedor',
                'verbose_name_plural': 'Vendedores',
            },
        ),
    ]
