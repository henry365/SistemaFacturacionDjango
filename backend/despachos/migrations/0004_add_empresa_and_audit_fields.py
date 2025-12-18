# Generated manually for adding empresa and audit fields to despachos

import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models
from django.utils import timezone
import uuid


def set_default_values(apps, schema_editor):
    """Establecer valores por defecto para registros existentes"""
    Despacho = apps.get_model('despachos', 'Despacho')
    now = timezone.now()

    for despacho in Despacho.objects.all():
        if not despacho.uuid:
            despacho.uuid = uuid.uuid4()
        if not despacho.fecha_creacion:
            despacho.fecha_creacion = despacho.fecha or now
        if not despacho.fecha_actualizacion:
            despacho.fecha_actualizacion = despacho.fecha or now
        despacho.save()


class Migration(migrations.Migration):

    dependencies = [
        ('empresas', '0001_initial'),
        ('despachos', '0003_initial'),
        ('inventario', '0003_add_empresa_and_audit_fields'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        # Despacho - empresa and audit fields
        migrations.AddField(
            model_name='despacho',
            name='empresa',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.PROTECT, related_name='despachos', to='empresas.empresa'),
        ),
        migrations.AddField(
            model_name='despacho',
            name='fecha_despacho',
            field=models.DateTimeField(blank=True, null=True, help_text='Fecha efectiva del despacho'),
        ),
        migrations.AddField(
            model_name='despacho',
            name='direccion_entrega',
            field=models.TextField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='despacho',
            name='transportista',
            field=models.CharField(blank=True, max_length=200, null=True),
        ),
        migrations.AddField(
            model_name='despacho',
            name='numero_guia',
            field=models.CharField(blank=True, max_length=100, null=True),
        ),
        migrations.AddField(
            model_name='despacho',
            name='observaciones',
            field=models.TextField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='despacho',
            name='uuid',
            field=models.UUIDField(default=uuid.uuid4, editable=False, null=True),
        ),
        migrations.AddField(
            model_name='despacho',
            name='fecha_creacion',
            field=models.DateTimeField(auto_now_add=True, null=True),
        ),
        migrations.AddField(
            model_name='despacho',
            name='fecha_actualizacion',
            field=models.DateTimeField(auto_now=True, null=True),
        ),
        migrations.AddField(
            model_name='despacho',
            name='usuario_creacion',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.PROTECT, related_name='despachos_creados', to=settings.AUTH_USER_MODEL),
        ),
        migrations.AddField(
            model_name='despacho',
            name='usuario_modificacion',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.PROTECT, related_name='despachos_modificados', to=settings.AUTH_USER_MODEL),
        ),
        migrations.AddField(
            model_name='despacho',
            name='usuario_despacho',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.PROTECT, related_name='despachos_realizados', to=settings.AUTH_USER_MODEL),
        ),

        # DetalleDespacho - additional fields
        migrations.AddField(
            model_name='detalledespacho',
            name='cantidad_solicitada',
            field=models.DecimalField(decimal_places=2, default=0, help_text='Cantidad en factura', max_digits=12),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='detalledespacho',
            name='cantidad_despachada',
            field=models.DecimalField(decimal_places=2, default=0, help_text='Cantidad efectivamente despachada', max_digits=12),
        ),
        migrations.AddField(
            model_name='detalledespacho',
            name='lote',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to='inventario.lote'),
        ),
        migrations.AddField(
            model_name='detalledespacho',
            name='observaciones',
            field=models.TextField(blank=True, null=True),
        ),

        # Alter estado field to add new choices
        migrations.AlterField(
            model_name='despacho',
            name='estado',
            field=models.CharField(choices=[('PENDIENTE', 'Pendiente'), ('EN_PREPARACION', 'En Preparación'), ('PARCIAL', 'Parcial'), ('COMPLETADO', 'Completado'), ('CANCELADO', 'Cancelado')], default='PENDIENTE', max_length=20),
        ),

        # Set default values for existing records
        migrations.RunPython(set_default_values, migrations.RunPython.noop),

        # Make uuid unique after setting values
        migrations.AlterField(
            model_name='despacho',
            name='uuid',
            field=models.UUIDField(default=uuid.uuid4, editable=False, unique=True),
        ),

        # Make fecha_creacion non-nullable
        migrations.AlterField(
            model_name='despacho',
            name='fecha_creacion',
            field=models.DateTimeField(auto_now_add=True),
        ),

        # Make fecha_actualizacion non-nullable
        migrations.AlterField(
            model_name='despacho',
            name='fecha_actualizacion',
            field=models.DateTimeField(auto_now=True),
        ),

        # Add ordering
        migrations.AlterModelOptions(
            name='despacho',
            options={'ordering': ['-fecha'], 'verbose_name': 'Despacho', 'verbose_name_plural': 'Despachos'},
        ),

        # Add verbose names for DetalleDespacho
        migrations.AlterModelOptions(
            name='detalledespacho',
            options={'verbose_name': 'Detalle de Despacho', 'verbose_name_plural': 'Detalles de Despachos'},
        ),

        # Alter cantidad field to have default
        migrations.AlterField(
            model_name='detalledespacho',
            name='cantidad',
            field=models.DecimalField(decimal_places=2, default=0, max_digits=12),
        ),
    ]
