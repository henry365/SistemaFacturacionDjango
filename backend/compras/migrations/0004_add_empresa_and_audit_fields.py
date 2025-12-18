# Generated manually for adding empresa and audit fields

import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models
from django.utils import timezone


def set_default_fechas(apps, schema_editor):
    """Establecer fechas por defecto para registros existentes"""
    timezone_now = timezone.now()
    
    # SolicitudCotizacionProveedor
    SolicitudCotizacionProveedor = apps.get_model('compras', 'SolicitudCotizacionProveedor')
    for solicitud in SolicitudCotizacionProveedor.objects.filter(fecha_creacion__isnull=True):
        solicitud.fecha_creacion = timezone_now
        solicitud.save(update_fields=['fecha_creacion'])
    
    # OrdenCompra
    OrdenCompra = apps.get_model('compras', 'OrdenCompra')
    for orden in OrdenCompra.objects.filter(fecha_creacion__isnull=True):
        orden.fecha_creacion = orden.fecha_emision
        orden.save(update_fields=['fecha_creacion'])
    
    # Compra
    Compra = apps.get_model('compras', 'Compra')
    for compra in Compra.objects.filter(fecha_creacion__isnull=True):
        compra.fecha_creacion = compra.fecha_registro
        compra.save(update_fields=['fecha_creacion'])
    
    # Gasto
    Gasto = apps.get_model('compras', 'Gasto')
    Gasto.objects.filter(fecha_actualizacion__isnull=True).update(fecha_actualizacion=timezone_now)


class Migration(migrations.Migration):

    dependencies = [
        ('empresas', '0001_initial'),
        ('compras', '0003_initial'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        # SolicitudCotizacionProveedor
        migrations.AddField(
            model_name='solicitudcotizacionproveedor',
            name='empresa',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.PROTECT, related_name='solicitudes_cotizacion', to='empresas.empresa'),
        ),
        migrations.AddField(
            model_name='solicitudcotizacionproveedor',
            name='fecha_creacion',
            field=models.DateTimeField(auto_now_add=True, null=True),
        ),
        migrations.AddField(
            model_name='solicitudcotizacionproveedor',
            name='fecha_actualizacion',
            field=models.DateTimeField(auto_now=True, null=True),
        ),
        migrations.AddField(
            model_name='solicitudcotizacionproveedor',
            name='usuario_modificacion',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.PROTECT, related_name='solicitudes_compra_modificadas', to=settings.AUTH_USER_MODEL),
        ),
        
        # OrdenCompra
        migrations.AddField(
            model_name='ordencompra',
            name='empresa',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.PROTECT, related_name='ordenes_compra', to='empresas.empresa'),
        ),
        migrations.AddField(
            model_name='ordencompra',
            name='fecha_creacion',
            field=models.DateTimeField(auto_now_add=True, null=True),
        ),
        migrations.AddField(
            model_name='ordencompra',
            name='fecha_actualizacion',
            field=models.DateTimeField(auto_now=True, null=True),
        ),
        migrations.AddField(
            model_name='ordencompra',
            name='usuario_modificacion',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.PROTECT, related_name='ordenes_compra_modificadas', to=settings.AUTH_USER_MODEL),
        ),
        
        # Compra - Primero eliminar unique_together existente
        migrations.AlterUniqueTogether(
            name='compra',
            unique_together=set(),
        ),
        migrations.AddField(
            model_name='compra',
            name='empresa',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.PROTECT, related_name='compras', to='empresas.empresa'),
        ),
        migrations.AddField(
            model_name='compra',
            name='fecha_creacion',
            field=models.DateTimeField(auto_now_add=True, null=True),
        ),
        migrations.AddField(
            model_name='compra',
            name='fecha_actualizacion',
            field=models.DateTimeField(auto_now=True, null=True),
        ),
        migrations.AddField(
            model_name='compra',
            name='usuario_modificacion',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.PROTECT, related_name='compras_modificadas', to=settings.AUTH_USER_MODEL),
        ),
        migrations.AlterUniqueTogether(
            name='compra',
            unique_together={('empresa', 'proveedor', 'numero_factura_proveedor')},
        ),
        
        # Gasto
        migrations.AddField(
            model_name='gasto',
            name='empresa',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.PROTECT, related_name='gastos', to='empresas.empresa'),
        ),
        migrations.AddField(
            model_name='gasto',
            name='fecha_actualizacion',
            field=models.DateTimeField(auto_now=True),
        ),
        migrations.AddField(
            model_name='gasto',
            name='usuario_modificacion',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.PROTECT, related_name='gastos_modificados', to=settings.AUTH_USER_MODEL),
        ),
        migrations.AddField(
            model_name='gasto',
            name='idempotency_key',
            field=models.CharField(blank=True, max_length=100, null=True, unique=True),
        ),
        
        # Ejecutar función para establecer fechas por defecto
        migrations.RunPython(set_default_fechas, migrations.RunPython.noop),
    ]

