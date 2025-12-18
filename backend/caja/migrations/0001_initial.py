# Generated manually for caja app
import uuid
from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='Caja',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('nombre', models.CharField(max_length=100)),
                ('descripcion', models.TextField(blank=True, null=True)),
                ('activa', models.BooleanField(default=True)),
                ('uuid', models.UUIDField(default=uuid.uuid4, editable=False, unique=True)),
                ('fecha_creacion', models.DateTimeField(auto_now_add=True)),
                ('usuario_creacion', models.ForeignKey(null=True, on_delete=django.db.models.deletion.PROTECT, related_name='cajas_creadas', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'verbose_name': 'Caja',
                'verbose_name_plural': 'Cajas',
            },
        ),
        migrations.CreateModel(
            name='SesionCaja',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('fecha_apertura', models.DateTimeField(auto_now_add=True)),
                ('monto_apertura', models.DecimalField(decimal_places=2, help_text='Monto inicial en efectivo', max_digits=14)),
                ('fecha_cierre', models.DateTimeField(blank=True, null=True)),
                ('monto_cierre_sistema', models.DecimalField(decimal_places=2, default=0, help_text='Calculado por el sistema', max_digits=14)),
                ('monto_cierre_usuario', models.DecimalField(blank=True, decimal_places=2, help_text='Declarado por el cajero', max_digits=14, null=True)),
                ('diferencia', models.DecimalField(decimal_places=2, default=0, max_digits=14)),
                ('estado', models.CharField(choices=[('ABIERTA', 'Abierta'), ('CERRADA', 'Cerrada'), ('ARQUEADA', 'Arqueada')], default='ABIERTA', max_length=20)),
                ('observaciones', models.TextField(blank=True, null=True)),
                ('uuid', models.UUIDField(default=uuid.uuid4, editable=False, unique=True)),
                ('caja', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name='sesiones', to='caja.caja')),
                ('usuario', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name='sesiones_caja', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'verbose_name': 'Sesión de Caja',
                'verbose_name_plural': 'Sesiones de Caja',
                'ordering': ['-fecha_apertura'],
            },
        ),
        migrations.CreateModel(
            name='MovimientoCaja',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('tipo_movimiento', models.CharField(choices=[('VENTA', 'Venta (Cobro)'), ('INGRESO_MANUAL', 'Ingreso Manual'), ('RETIRO_MANUAL', 'Retiro Manual'), ('GASTO_MENOR', 'Gasto Menor'), ('APERTURA', 'Monto Apertura'), ('CIERRE', 'Retiro por Cierre')], max_length=20)),
                ('monto', models.DecimalField(decimal_places=2, max_digits=14)),
                ('descripcion', models.CharField(max_length=255)),
                ('fecha', models.DateTimeField(auto_now_add=True)),
                ('referencia', models.CharField(blank=True, help_text='ID Factura, Recibo, etc.', max_length=100, null=True)),
                ('uuid', models.UUIDField(default=uuid.uuid4, editable=False, unique=True)),
                ('sesion', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name='movimientos', to='caja.sesioncaja')),
                ('usuario', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'verbose_name': 'Movimiento de Caja',
                'verbose_name_plural': 'Movimientos de Caja',
                'ordering': ['-fecha'],
            },
        ),
    ]
