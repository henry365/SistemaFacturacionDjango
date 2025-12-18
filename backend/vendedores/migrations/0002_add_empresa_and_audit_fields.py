# Generated manually for adding empresa, uuid and audit fields

import uuid
import django.core.validators
import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


def generate_uuid_for_existing_vendedores(apps, schema_editor):
    """Generar UUIDs únicos para vendedores existentes"""
    Vendedor = apps.get_model('vendedores', 'Vendedor')
    for vendedor in Vendedor.objects.all():
        if not vendedor.uuid:
            vendedor.uuid = uuid.uuid4()
            vendedor.save(update_fields=['uuid'])


class Migration(migrations.Migration):

    dependencies = [
        ('empresas', '0001_initial'),
        ('vendedores', '0001_initial'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        # Primero eliminar unique de cedula
        migrations.AlterField(
            model_name='vendedor',
            name='cedula',
            field=models.CharField(blank=True, max_length=20, null=True),
        ),
        # Agregar campo empresa (nullable)
        migrations.AddField(
            model_name='vendedor',
            name='empresa',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.PROTECT, related_name='vendedores', to='empresas.empresa'),
        ),
        # Agregar campo uuid sin unique primero
        migrations.AddField(
            model_name='vendedor',
            name='uuid',
            field=models.UUIDField(default=uuid.uuid4, editable=False, null=True),
        ),
        # Generar UUIDs para registros existentes
        migrations.RunPython(generate_uuid_for_existing_vendedores, migrations.RunPython.noop),
        # Ahora hacer uuid unique y no nullable
        migrations.AlterField(
            model_name='vendedor',
            name='uuid',
            field=models.UUIDField(default=uuid.uuid4, editable=False, unique=True),
        ),
        # Agregar campos de auditoría
        migrations.AddField(
            model_name='vendedor',
            name='usuario_creacion',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.PROTECT, related_name='vendedores_creados', to=settings.AUTH_USER_MODEL),
        ),
        migrations.AddField(
            model_name='vendedor',
            name='usuario_modificacion',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.PROTECT, related_name='vendedores_modificados', to=settings.AUTH_USER_MODEL),
        ),
        # Agregar validadores a comision_porcentaje
        migrations.AlterField(
            model_name='vendedor',
            name='comision_porcentaje',
            field=models.DecimalField(decimal_places=2, default=0.0, help_text='Porcentaje de comisión por ventas (0-100)', max_digits=5, validators=[django.core.validators.MinValueValidator(0), django.core.validators.MaxValueValidator(100)]),
        ),
        # Actualizar unique_together
        migrations.AlterUniqueTogether(
            name='vendedor',
            unique_together={('empresa', 'cedula')},
        ),
    ]

