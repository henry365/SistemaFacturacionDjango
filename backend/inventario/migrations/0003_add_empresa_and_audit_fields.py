# Generated manually for adding empresa and audit fields

import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models
from django.utils import timezone


def set_default_fechas(apps, schema_editor):
    """Establecer fechas por defecto para registros existentes"""
    timezone_now = timezone.now()
    
    # Almacen
    Almacen = apps.get_model('inventario', 'Almacen')
    Almacen.objects.filter(fecha_creacion__isnull=True).update(fecha_creacion=timezone_now)
    
    # InventarioProducto
    InventarioProducto = apps.get_model('inventario', 'InventarioProducto')
    InventarioProducto.objects.filter(fecha_creacion__isnull=True).update(fecha_creacion=timezone_now)
    
    # MovimientoInventario - usar fecha existente
    MovimientoInventario = apps.get_model('inventario', 'MovimientoInventario')
    for movimiento in MovimientoInventario.objects.filter(fecha_actualizacion__isnull=True):
        movimiento.fecha_actualizacion = movimiento.fecha
        movimiento.save(update_fields=['fecha_actualizacion'])
    
    # ReservaStock
    ReservaStock = apps.get_model('inventario', 'ReservaStock')
    ReservaStock.objects.filter(fecha_creacion__isnull=True).update(fecha_creacion=timezone_now)
    
    # Lote
    Lote = apps.get_model('inventario', 'Lote')
    for lote in Lote.objects.filter(fecha_creacion__isnull=True):
        lote.fecha_creacion = lote.fecha_ingreso
        lote.save(update_fields=['fecha_creacion'])
    
    # AlertaInventario
    AlertaInventario = apps.get_model('inventario', 'AlertaInventario')
    for alerta in AlertaInventario.objects.filter(fecha_creacion__isnull=True):
        alerta.fecha_creacion = alerta.fecha_alerta
        alerta.save(update_fields=['fecha_creacion'])
    
    # TransferenciaInventario
    TransferenciaInventario = apps.get_model('inventario', 'TransferenciaInventario')
    for transferencia in TransferenciaInventario.objects.filter(fecha_creacion__isnull=True):
        transferencia.fecha_creacion = transferencia.fecha_solicitud
        transferencia.save(update_fields=['fecha_creacion'])
    
    # AjusteInventario
    AjusteInventario = apps.get_model('inventario', 'AjusteInventario')
    AjusteInventario.objects.filter(fecha_creacion__isnull=True).update(fecha_creacion=timezone_now)
    
    # ConteoFisico
    ConteoFisico = apps.get_model('inventario', 'ConteoFisico')
    ConteoFisico.objects.filter(fecha_creacion__isnull=True).update(fecha_creacion=timezone_now)


class Migration(migrations.Migration):

    dependencies = [
        ('empresas', '0001_initial'),
        ('inventario', '0002_initial'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        # Almacen
        migrations.AlterUniqueTogether(
            name='almacen',
            unique_together=set(),
        ),
        migrations.AddField(
            model_name='almacen',
            name='empresa',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.PROTECT, related_name='almacenes', to='empresas.empresa'),
        ),
        migrations.AddField(
            model_name='almacen',
            name='fecha_creacion',
            field=models.DateTimeField(auto_now_add=True, null=True),
        ),
        migrations.AddField(
            model_name='almacen',
            name='fecha_actualizacion',
            field=models.DateTimeField(auto_now=True, null=True),
        ),
        migrations.AddField(
            model_name='almacen',
            name='usuario_creacion',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.PROTECT, related_name='almacenes_creados', to=settings.AUTH_USER_MODEL),
        ),
        migrations.AddField(
            model_name='almacen',
            name='usuario_modificacion',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.PROTECT, related_name='almacenes_modificados', to=settings.AUTH_USER_MODEL),
        ),
        migrations.AlterUniqueTogether(
            name='almacen',
            unique_together={('empresa', 'nombre')},
        ),
        
        # InventarioProducto
        migrations.AddField(
            model_name='inventarioproducto',
            name='empresa',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.PROTECT, related_name='inventarios_productos', to='empresas.empresa'),
        ),
        migrations.AddField(
            model_name='inventarioproducto',
            name='fecha_creacion',
            field=models.DateTimeField(auto_now_add=True, null=True),
        ),
        migrations.AddField(
            model_name='inventarioproducto',
            name='fecha_actualizacion',
            field=models.DateTimeField(auto_now=True, null=True),
        ),
        migrations.AddField(
            model_name='inventarioproducto',
            name='usuario_creacion',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.PROTECT, related_name='inventarios_productos_creados', to=settings.AUTH_USER_MODEL),
        ),
        migrations.AddField(
            model_name='inventarioproducto',
            name='usuario_modificacion',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.PROTECT, related_name='inventarios_productos_modificados', to=settings.AUTH_USER_MODEL),
        ),
        
        # MovimientoInventario
        migrations.AddField(
            model_name='movimientoinventario',
            name='empresa',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.PROTECT, related_name='movimientos_inventario', to='empresas.empresa'),
        ),
        migrations.AddField(
            model_name='movimientoinventario',
            name='fecha_actualizacion',
            field=models.DateTimeField(auto_now=True, null=True),
        ),
        migrations.AddField(
            model_name='movimientoinventario',
            name='usuario_creacion',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.PROTECT, related_name='movimientos_inventario_creados', to=settings.AUTH_USER_MODEL),
        ),
        migrations.AddField(
            model_name='movimientoinventario',
            name='usuario_modificacion',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.PROTECT, related_name='movimientos_inventario_modificados', to=settings.AUTH_USER_MODEL),
        ),
        migrations.AlterField(
            model_name='movimientoinventario',
            name='usuario',
            field=models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name='movimientos_realizados', to=settings.AUTH_USER_MODEL),
        ),
        
        # ReservaStock
        migrations.AddField(
            model_name='reservastock',
            name='empresa',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.PROTECT, related_name='reservas_stock', to='empresas.empresa'),
        ),
        migrations.AddField(
            model_name='reservastock',
            name='fecha_creacion',
            field=models.DateTimeField(auto_now_add=True, null=True),
        ),
        migrations.AddField(
            model_name='reservastock',
            name='fecha_actualizacion',
            field=models.DateTimeField(auto_now=True, null=True),
        ),
        migrations.AddField(
            model_name='reservastock',
            name='usuario_creacion',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.PROTECT, related_name='reservas_stock_creadas', to=settings.AUTH_USER_MODEL),
        ),
        migrations.AddField(
            model_name='reservastock',
            name='usuario_modificacion',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.PROTECT, related_name='reservas_stock_modificadas', to=settings.AUTH_USER_MODEL),
        ),
        migrations.AlterField(
            model_name='reservastock',
            name='usuario',
            field=models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name='reservas_realizadas', to=settings.AUTH_USER_MODEL),
        ),
        
        # Lote
        migrations.AlterUniqueTogether(
            name='lote',
            unique_together=set(),
        ),
        migrations.AddField(
            model_name='lote',
            name='empresa',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.PROTECT, related_name='lotes', to='empresas.empresa'),
        ),
        migrations.AddField(
            model_name='lote',
            name='fecha_creacion',
            field=models.DateTimeField(auto_now_add=True, null=True),
        ),
        migrations.AddField(
            model_name='lote',
            name='fecha_actualizacion',
            field=models.DateTimeField(auto_now=True, null=True),
        ),
        migrations.AddField(
            model_name='lote',
            name='usuario_creacion',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.PROTECT, related_name='lotes_creados', to=settings.AUTH_USER_MODEL),
        ),
        migrations.AddField(
            model_name='lote',
            name='usuario_modificacion',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.PROTECT, related_name='lotes_modificados', to=settings.AUTH_USER_MODEL),
        ),
        migrations.AlterUniqueTogether(
            name='lote',
            unique_together={('empresa', 'producto', 'almacen', 'codigo_lote')},
        ),
        
        # AlertaInventario
        migrations.AddField(
            model_name='alertainventario',
            name='empresa',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.PROTECT, related_name='alertas_inventario', to='empresas.empresa'),
        ),
        migrations.AddField(
            model_name='alertainventario',
            name='fecha_creacion',
            field=models.DateTimeField(auto_now_add=True, null=True),
        ),
        migrations.AddField(
            model_name='alertainventario',
            name='fecha_actualizacion',
            field=models.DateTimeField(auto_now=True, null=True),
        ),
        migrations.AddField(
            model_name='alertainventario',
            name='usuario_creacion',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.PROTECT, related_name='alertas_inventario_creadas', to=settings.AUTH_USER_MODEL),
        ),
        migrations.AddField(
            model_name='alertainventario',
            name='usuario_modificacion',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.PROTECT, related_name='alertas_inventario_modificadas', to=settings.AUTH_USER_MODEL),
        ),
        migrations.AlterField(
            model_name='alertainventario',
            name='usuario_resolucion',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='alertas_resueltas', to=settings.AUTH_USER_MODEL),
        ),
        
        # TransferenciaInventario
        migrations.AlterUniqueTogether(
            name='transferenciainventario',
            unique_together=set(),
        ),
        migrations.AddField(
            model_name='transferenciainventario',
            name='empresa',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.PROTECT, related_name='transferencias_inventario', to='empresas.empresa'),
        ),
        migrations.AddField(
            model_name='transferenciainventario',
            name='fecha_creacion',
            field=models.DateTimeField(auto_now_add=True, null=True),
        ),
        migrations.AddField(
            model_name='transferenciainventario',
            name='fecha_actualizacion',
            field=models.DateTimeField(auto_now=True, null=True),
        ),
        migrations.AddField(
            model_name='transferenciainventario',
            name='usuario_creacion',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.PROTECT, related_name='transferencias_inventario_creadas', to=settings.AUTH_USER_MODEL),
        ),
        migrations.AddField(
            model_name='transferenciainventario',
            name='usuario_modificacion',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.PROTECT, related_name='transferencias_inventario_modificadas', to=settings.AUTH_USER_MODEL),
        ),
        migrations.AlterField(
            model_name='transferenciainventario',
            name='numero_transferencia',
            field=models.CharField(max_length=50),
        ),
        migrations.AlterUniqueTogether(
            name='transferenciainventario',
            unique_together={('empresa', 'numero_transferencia')},
        ),
        
        # AjusteInventario
        migrations.AddField(
            model_name='ajusteinventario',
            name='empresa',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.PROTECT, related_name='ajustes_inventario', to='empresas.empresa'),
        ),
        migrations.AddField(
            model_name='ajusteinventario',
            name='fecha_creacion',
            field=models.DateTimeField(auto_now_add=True, null=True),
        ),
        migrations.AddField(
            model_name='ajusteinventario',
            name='fecha_actualizacion',
            field=models.DateTimeField(auto_now=True, null=True),
        ),
        migrations.AddField(
            model_name='ajusteinventario',
            name='usuario_creacion',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.PROTECT, related_name='ajustes_inventario_creados', to=settings.AUTH_USER_MODEL),
        ),
        migrations.AddField(
            model_name='ajusteinventario',
            name='usuario_modificacion',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.PROTECT, related_name='ajustes_inventario_modificados', to=settings.AUTH_USER_MODEL),
        ),
        
        # ConteoFisico
        migrations.AlterUniqueTogether(
            name='conteofisico',
            unique_together=set(),
        ),
        migrations.AddField(
            model_name='conteofisico',
            name='empresa',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.PROTECT, related_name='conteos_fisicos', to='empresas.empresa'),
        ),
        migrations.AddField(
            model_name='conteofisico',
            name='fecha_creacion',
            field=models.DateTimeField(auto_now_add=True, null=True),
        ),
        migrations.AddField(
            model_name='conteofisico',
            name='fecha_actualizacion',
            field=models.DateTimeField(auto_now=True, null=True),
        ),
        migrations.AddField(
            model_name='conteofisico',
            name='usuario_creacion',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.PROTECT, related_name='conteos_fisicos_creados', to=settings.AUTH_USER_MODEL),
        ),
        migrations.AddField(
            model_name='conteofisico',
            name='usuario_modificacion',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.PROTECT, related_name='conteos_fisicos_modificados', to=settings.AUTH_USER_MODEL),
        ),
        migrations.AlterField(
            model_name='conteofisico',
            name='numero_conteo',
            field=models.CharField(max_length=50),
        ),
        migrations.AlterField(
            model_name='conteofisico',
            name='usuario_responsable',
            field=models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name='conteos_responsables', to=settings.AUTH_USER_MODEL),
        ),
        migrations.AlterUniqueTogether(
            name='conteofisico',
            unique_together={('empresa', 'numero_conteo')},
        ),
        
        # Ejecutar función para establecer fechas por defecto
        migrations.RunPython(set_default_fechas, migrations.RunPython.noop),
        
        # Hacer campos fecha_creacion no nullable después de establecer valores
        migrations.AlterField(
            model_name='almacen',
            name='fecha_creacion',
            field=models.DateTimeField(auto_now_add=True),
        ),
        migrations.AlterField(
            model_name='inventarioproducto',
            name='fecha_creacion',
            field=models.DateTimeField(auto_now_add=True),
        ),
        migrations.AlterField(
            model_name='reservastock',
            name='fecha_creacion',
            field=models.DateTimeField(auto_now_add=True),
        ),
        migrations.AlterField(
            model_name='lote',
            name='fecha_creacion',
            field=models.DateTimeField(auto_now_add=True),
        ),
        migrations.AlterField(
            model_name='alertainventario',
            name='fecha_creacion',
            field=models.DateTimeField(auto_now_add=True),
        ),
        migrations.AlterField(
            model_name='transferenciainventario',
            name='fecha_creacion',
            field=models.DateTimeField(auto_now_add=True),
        ),
        migrations.AlterField(
            model_name='ajusteinventario',
            name='fecha_creacion',
            field=models.DateTimeField(auto_now_add=True),
        ),
        migrations.AlterField(
            model_name='conteofisico',
            name='fecha_creacion',
            field=models.DateTimeField(auto_now_add=True),
        ),
        migrations.AlterField(
            model_name='movimientoinventario',
            name='fecha_actualizacion',
            field=models.DateTimeField(auto_now=True),
        ),
    ]

