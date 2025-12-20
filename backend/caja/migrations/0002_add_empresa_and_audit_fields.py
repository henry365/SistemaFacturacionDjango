# Generated manually for caja app - Add empresa and audit fields
import uuid
from decimal import Decimal
from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion
from django.utils import timezone


def set_default_dates(apps, schema_editor):
    """Set default dates for existing records."""
    SesionCaja = apps.get_model('caja', 'SesionCaja')
    MovimientoCaja = apps.get_model('caja', 'MovimientoCaja')

    now = timezone.now()

    # Update SesionCaja records
    for sesion in SesionCaja.objects.filter(fecha_creacion__isnull=True):
        sesion.fecha_creacion = sesion.fecha_apertura or now
        sesion.fecha_actualizacion = now
        sesion.save(update_fields=['fecha_creacion', 'fecha_actualizacion'])

    # Update MovimientoCaja records
    for mov in MovimientoCaja.objects.filter(fecha_creacion__isnull=True):
        mov.fecha_creacion = mov.fecha or now
        mov.fecha_actualizacion = now
        mov.save(update_fields=['fecha_creacion', 'fecha_actualizacion'])


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('empresas', '0001_initial'),
        ('caja', '0001_initial'),
    ]

    operations = [
        # ========== CAJA MODEL ==========
        # Add empresa field to Caja
        migrations.AddField(
            model_name='caja',
            name='empresa',
            field=models.ForeignKey(
                blank=True,
                db_index=True,
                help_text='Empresa a la que pertenece la caja',
                null=True,
                on_delete=django.db.models.deletion.PROTECT,
                related_name='cajas',
                to='empresas.empresa'
            ),
        ),
        # Add fecha_actualizacion to Caja
        migrations.AddField(
            model_name='caja',
            name='fecha_actualizacion',
            field=models.DateTimeField(auto_now=True),
        ),
        # Add usuario_modificacion to Caja
        migrations.AddField(
            model_name='caja',
            name='usuario_modificacion',
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name='cajas_modificadas',
                to=settings.AUTH_USER_MODEL
            ),
        ),
        # Change usuario_creacion on_delete to SET_NULL
        migrations.AlterField(
            model_name='caja',
            name='usuario_creacion',
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name='cajas_creadas',
                to=settings.AUTH_USER_MODEL
            ),
        ),
        # Add unique_together for Caja
        migrations.AlterUniqueTogether(
            name='caja',
            unique_together={('empresa', 'nombre')},
        ),
        # Add indexes for Caja
        migrations.AddIndex(
            model_name='caja',
            index=models.Index(fields=['empresa', 'activa'], name='caja_caja_empresa_7a8d13_idx'),
        ),
        migrations.AddIndex(
            model_name='caja',
            index=models.Index(fields=['empresa', 'nombre'], name='caja_caja_empresa_a1b2c3_idx'),
        ),

        # ========== SESIONCAJA MODEL ==========
        # Add empresa field to SesionCaja
        migrations.AddField(
            model_name='sesioncaja',
            name='empresa',
            field=models.ForeignKey(
                blank=True,
                db_index=True,
                help_text='Empresa a la que pertenece la sesión',
                null=True,
                on_delete=django.db.models.deletion.PROTECT,
                related_name='sesiones_caja',
                to='empresas.empresa'
            ),
        ),
        # Add fecha_creacion to SesionCaja (nullable first)
        migrations.AddField(
            model_name='sesioncaja',
            name='fecha_creacion',
            field=models.DateTimeField(auto_now_add=True, null=True),
        ),
        # Add fecha_actualizacion to SesionCaja
        migrations.AddField(
            model_name='sesioncaja',
            name='fecha_actualizacion',
            field=models.DateTimeField(auto_now=True),
        ),
        # Add usuario_creacion to SesionCaja
        migrations.AddField(
            model_name='sesioncaja',
            name='usuario_creacion',
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name='sesiones_caja_creadas',
                to=settings.AUTH_USER_MODEL
            ),
        ),
        # Add usuario_modificacion to SesionCaja
        migrations.AddField(
            model_name='sesioncaja',
            name='usuario_modificacion',
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name='sesiones_caja_modificadas',
                to=settings.AUTH_USER_MODEL
            ),
        ),
        # Add db_index to estado field
        migrations.AlterField(
            model_name='sesioncaja',
            name='estado',
            field=models.CharField(
                choices=[('ABIERTA', 'Abierta'), ('CERRADA', 'Cerrada'), ('ARQUEADA', 'Arqueada')],
                db_index=True,
                default='ABIERTA',
                max_length=20
            ),
        ),
        # Add indexes for SesionCaja
        migrations.AddIndex(
            model_name='sesioncaja',
            index=models.Index(fields=['empresa', 'estado'], name='caja_sesion_empresa_d1e2f3_idx'),
        ),
        migrations.AddIndex(
            model_name='sesioncaja',
            index=models.Index(fields=['empresa', 'fecha_apertura'], name='caja_sesion_empresa_g4h5i6_idx'),
        ),
        migrations.AddIndex(
            model_name='sesioncaja',
            index=models.Index(fields=['caja', 'estado'], name='caja_sesion_caja_id_j7k8l9_idx'),
        ),

        # ========== MOVIMIENTOCAJA MODEL ==========
        # Add empresa field to MovimientoCaja
        migrations.AddField(
            model_name='movimientocaja',
            name='empresa',
            field=models.ForeignKey(
                blank=True,
                db_index=True,
                help_text='Empresa a la que pertenece el movimiento',
                null=True,
                on_delete=django.db.models.deletion.PROTECT,
                related_name='movimientos_caja',
                to='empresas.empresa'
            ),
        ),
        # Add fecha_creacion to MovimientoCaja (nullable first)
        migrations.AddField(
            model_name='movimientocaja',
            name='fecha_creacion',
            field=models.DateTimeField(auto_now_add=True, null=True),
        ),
        # Add fecha_actualizacion to MovimientoCaja
        migrations.AddField(
            model_name='movimientocaja',
            name='fecha_actualizacion',
            field=models.DateTimeField(auto_now=True),
        ),
        # Add usuario_creacion to MovimientoCaja
        migrations.AddField(
            model_name='movimientocaja',
            name='usuario_creacion',
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name='movimientos_caja_creados',
                to=settings.AUTH_USER_MODEL
            ),
        ),
        # Add usuario_modificacion to MovimientoCaja
        migrations.AddField(
            model_name='movimientocaja',
            name='usuario_modificacion',
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name='movimientos_caja_modificados',
                to=settings.AUTH_USER_MODEL
            ),
        ),
        # Change usuario related_name
        migrations.AlterField(
            model_name='movimientocaja',
            name='usuario',
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.PROTECT,
                related_name='movimientos_caja',
                to=settings.AUTH_USER_MODEL
            ),
        ),
        # Add db_index to tipo_movimiento
        migrations.AlterField(
            model_name='movimientocaja',
            name='tipo_movimiento',
            field=models.CharField(
                choices=[
                    ('VENTA', 'Venta (Cobro)'),
                    ('INGRESO_MANUAL', 'Ingreso Manual'),
                    ('RETIRO_MANUAL', 'Retiro Manual'),
                    ('GASTO_MENOR', 'Gasto Menor'),
                    ('APERTURA', 'Monto Apertura'),
                    ('CIERRE', 'Retiro por Cierre')
                ],
                db_index=True,
                max_length=20
            ),
        ),
        # Add indexes for MovimientoCaja
        migrations.AddIndex(
            model_name='movimientocaja',
            index=models.Index(fields=['empresa', 'tipo_movimiento'], name='caja_movimi_empresa_m1n2o3_idx'),
        ),
        migrations.AddIndex(
            model_name='movimientocaja',
            index=models.Index(fields=['empresa', 'fecha'], name='caja_movimi_empresa_p4q5r6_idx'),
        ),
        migrations.AddIndex(
            model_name='movimientocaja',
            index=models.Index(fields=['sesion', 'tipo_movimiento'], name='caja_movimi_sesion__s7t8u9_idx'),
        ),

        # Run data migration for dates
        migrations.RunPython(set_default_dates, migrations.RunPython.noop),
    ]
