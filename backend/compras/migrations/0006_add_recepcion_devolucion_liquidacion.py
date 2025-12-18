# Generated manually
from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion
import uuid


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('empresas', '0001_initial'),
        ('inventario', '0003_add_empresa_and_audit_fields'),
        ('proveedores', '0001_initial'),
        ('productos', '0001_initial'),
        ('compras', '0005_alter_compra_options_alter_gasto_options_and_more'),
    ]

    operations = [
        # RecepcionCompra
        migrations.CreateModel(
            name='RecepcionCompra',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('numero_recepcion', models.CharField(editable=False, max_length=20, unique=True)),
                ('fecha_recepcion', models.DateField(db_index=True)),
                ('estado', models.CharField(choices=[('PENDIENTE', 'Pendiente'), ('PARCIAL', 'Parcialmente Recibida'), ('COMPLETA', 'Completamente Recibida'), ('CANCELADA', 'Cancelada')], db_index=True, default='PENDIENTE', max_length=20)),
                ('observaciones', models.TextField(blank=True)),
                ('fecha_creacion', models.DateTimeField(auto_now_add=True)),
                ('fecha_actualizacion', models.DateTimeField(auto_now=True)),
                ('uuid', models.UUIDField(default=uuid.uuid4, editable=False, unique=True)),
                ('idempotency_key', models.CharField(blank=True, max_length=100, null=True, unique=True)),
                ('almacen', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name='recepciones_compra', to='inventario.almacen')),
                ('empresa', models.ForeignKey(db_index=True, on_delete=django.db.models.deletion.PROTECT, related_name='recepciones_compra', to='empresas.empresa')),
                ('orden_compra', models.ForeignKey(db_index=True, on_delete=django.db.models.deletion.PROTECT, related_name='recepciones', to='compras.ordencompra')),
                ('usuario_creacion', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.PROTECT, related_name='recepciones_compra_creadas', to=settings.AUTH_USER_MODEL)),
                ('usuario_modificacion', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.PROTECT, related_name='recepciones_compra_modificadas', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'verbose_name': 'Recepción de Compra',
                'verbose_name_plural': 'Recepciones de Compra',
                'ordering': ['-fecha_recepcion'],
            },
        ),
        migrations.AddIndex(
            model_name='recepcioncompra',
            index=models.Index(fields=['empresa', 'estado'], name='compras_rec_empresa_7e8c7c_idx'),
        ),
        migrations.AddIndex(
            model_name='recepcioncompra',
            index=models.Index(fields=['orden_compra', 'estado'], name='compras_rec_orden_c_a7e8b1_idx'),
        ),
        migrations.AddIndex(
            model_name='recepcioncompra',
            index=models.Index(fields=['empresa', 'fecha_recepcion'], name='compras_rec_empresa_f1b3c2_idx'),
        ),

        # DetalleRecepcion
        migrations.CreateModel(
            name='DetalleRecepcion',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('cantidad_ordenada', models.DecimalField(decimal_places=2, max_digits=12)),
                ('cantidad_recibida', models.DecimalField(decimal_places=2, max_digits=12)),
                ('cantidad_rechazada', models.DecimalField(decimal_places=2, default=0, max_digits=12)),
                ('numero_lote', models.CharField(blank=True, help_text='Número de lote del proveedor', max_length=50, null=True)),
                ('fecha_vencimiento', models.DateField(blank=True, null=True)),
                ('observaciones', models.TextField(blank=True)),
                ('detalle_orden', models.ForeignKey(db_index=True, on_delete=django.db.models.deletion.PROTECT, related_name='recepciones', to='compras.detalleordencompra')),
                ('lote', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='recepciones', to='inventario.lote')),
                ('producto', models.ForeignKey(db_index=True, on_delete=django.db.models.deletion.PROTECT, to='productos.producto')),
                ('recepcion', models.ForeignKey(db_index=True, on_delete=django.db.models.deletion.CASCADE, related_name='detalles', to='compras.recepcioncompra')),
            ],
            options={
                'verbose_name': 'Detalle de Recepción',
                'verbose_name_plural': 'Detalles de Recepción',
            },
        ),
        migrations.AddIndex(
            model_name='detallerecepcion',
            index=models.Index(fields=['recepcion', 'producto'], name='compras_det_recepci_7a8b3c_idx'),
        ),

        # DevolucionProveedor
        migrations.CreateModel(
            name='DevolucionProveedor',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('numero_devolucion', models.CharField(editable=False, max_length=20, unique=True)),
                ('fecha', models.DateField(db_index=True)),
                ('motivo', models.CharField(choices=[('DEFECTO', 'Producto Defectuoso'), ('ERROR', 'Error en Pedido'), ('GARANTIA', 'Garantía'), ('CADUCADO', 'Producto Caducado'), ('DANADO', 'Producto Dañado'), ('OTRO', 'Otro')], default='DEFECTO', max_length=20)),
                ('descripcion_motivo', models.TextField(blank=True)),
                ('estado', models.CharField(choices=[('BORRADOR', 'Borrador'), ('CONFIRMADA', 'Confirmada'), ('ENVIADA', 'Enviada al Proveedor'), ('ACEPTADA', 'Aceptada por Proveedor'), ('CANCELADA', 'Cancelada')], db_index=True, default='BORRADOR', max_length=20)),
                ('subtotal', models.DecimalField(decimal_places=2, default=0, max_digits=14)),
                ('impuestos', models.DecimalField(decimal_places=2, default=0, max_digits=14)),
                ('total', models.DecimalField(decimal_places=2, default=0, max_digits=14)),
                ('genera_nota_credito', models.BooleanField(default=True, help_text='Si es True, genera ajuste en CxP')),
                ('fecha_creacion', models.DateTimeField(auto_now_add=True)),
                ('fecha_actualizacion', models.DateTimeField(auto_now=True)),
                ('uuid', models.UUIDField(default=uuid.uuid4, editable=False, unique=True)),
                ('idempotency_key', models.CharField(blank=True, max_length=100, null=True, unique=True)),
                ('compra', models.ForeignKey(blank=True, db_index=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='devoluciones', to='compras.compra')),
                ('empresa', models.ForeignKey(db_index=True, on_delete=django.db.models.deletion.PROTECT, related_name='devoluciones_proveedor', to='empresas.empresa')),
                ('proveedor', models.ForeignKey(db_index=True, on_delete=django.db.models.deletion.PROTECT, related_name='devoluciones', to='proveedores.proveedor')),
                ('usuario_creacion', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.PROTECT, related_name='devoluciones_proveedor_creadas', to=settings.AUTH_USER_MODEL)),
                ('usuario_modificacion', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.PROTECT, related_name='devoluciones_proveedor_modificadas', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'verbose_name': 'Devolución a Proveedor',
                'verbose_name_plural': 'Devoluciones a Proveedores',
                'ordering': ['-fecha'],
            },
        ),
        migrations.AddIndex(
            model_name='devolucionproveedor',
            index=models.Index(fields=['empresa', 'estado'], name='compras_dev_empresa_a1b2c3_idx'),
        ),
        migrations.AddIndex(
            model_name='devolucionproveedor',
            index=models.Index(fields=['proveedor', 'estado'], name='compras_dev_proveed_d4e5f6_idx'),
        ),
        migrations.AddIndex(
            model_name='devolucionproveedor',
            index=models.Index(fields=['empresa', 'fecha'], name='compras_dev_empresa_g7h8i9_idx'),
        ),

        # DetalleDevolucionProveedor
        migrations.CreateModel(
            name='DetalleDevolucionProveedor',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('cantidad', models.DecimalField(decimal_places=2, max_digits=12)),
                ('costo_unitario', models.DecimalField(decimal_places=2, max_digits=12)),
                ('impuesto', models.DecimalField(decimal_places=2, default=0, max_digits=12)),
                ('observaciones', models.TextField(blank=True)),
                ('almacen', models.ForeignKey(db_index=True, on_delete=django.db.models.deletion.PROTECT, related_name='devoluciones_proveedor', to='inventario.almacen')),
                ('devolucion', models.ForeignKey(db_index=True, on_delete=django.db.models.deletion.CASCADE, related_name='detalles', to='compras.devolucionproveedor')),
                ('lote', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to='inventario.lote')),
                ('producto', models.ForeignKey(db_index=True, on_delete=django.db.models.deletion.PROTECT, to='productos.producto')),
            ],
            options={
                'verbose_name': 'Detalle de Devolución',
                'verbose_name_plural': 'Detalles de Devolución',
            },
        ),
        migrations.AddIndex(
            model_name='detalledevolucionproveedor',
            index=models.Index(fields=['devolucion', 'producto'], name='compras_det_devoluc_j1k2l3_idx'),
        ),

        # LiquidacionImportacion
        migrations.CreateModel(
            name='LiquidacionImportacion',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('numero_liquidacion', models.CharField(editable=False, max_length=20, unique=True)),
                ('fecha', models.DateField(db_index=True)),
                ('incoterm', models.CharField(choices=[('FOB', 'FOB - Free On Board'), ('CIF', 'CIF - Cost, Insurance and Freight'), ('EXW', 'EXW - Ex Works'), ('FCA', 'FCA - Free Carrier'), ('CFR', 'CFR - Cost and Freight'), ('DAP', 'DAP - Delivered at Place'), ('DDP', 'DDP - Delivered Duty Paid')], default='FOB', max_length=3)),
                ('metodo_prorrateo', models.CharField(choices=[('VALOR', 'Por Valor FOB'), ('PESO', 'Por Peso'), ('VOLUMEN', 'Por Volumen'), ('UNIDADES', 'Por Unidades')], default='VALOR', max_length=10)),
                ('tasa_cambio', models.DecimalField(decimal_places=4, default=1.0, max_digits=10)),
                ('total_fob', models.DecimalField(decimal_places=2, default=0, help_text='Valor FOB de la mercancía', max_digits=14)),
                ('total_gastos', models.DecimalField(decimal_places=2, default=0, help_text='Total de gastos de importación', max_digits=14)),
                ('total_cif', models.DecimalField(decimal_places=2, default=0, help_text='Costo total nacionalizado', max_digits=14)),
                ('estado', models.CharField(choices=[('BORRADOR', 'Borrador'), ('LIQUIDADA', 'Liquidada'), ('CANCELADA', 'Cancelada')], db_index=True, default='BORRADOR', max_length=20)),
                ('observaciones', models.TextField(blank=True)),
                ('fecha_creacion', models.DateTimeField(auto_now_add=True)),
                ('fecha_actualizacion', models.DateTimeField(auto_now=True)),
                ('uuid', models.UUIDField(default=uuid.uuid4, editable=False, unique=True)),
                ('idempotency_key', models.CharField(blank=True, max_length=100, null=True, unique=True)),
                ('compra', models.ForeignKey(db_index=True, on_delete=django.db.models.deletion.PROTECT, related_name='liquidaciones', to='compras.compra')),
                ('empresa', models.ForeignKey(db_index=True, on_delete=django.db.models.deletion.PROTECT, related_name='liquidaciones_importacion', to='empresas.empresa')),
                ('usuario_creacion', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.PROTECT, related_name='liquidaciones_creadas', to=settings.AUTH_USER_MODEL)),
                ('usuario_modificacion', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.PROTECT, related_name='liquidaciones_modificadas', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'verbose_name': 'Liquidación de Importación',
                'verbose_name_plural': 'Liquidaciones de Importación',
                'ordering': ['-fecha'],
            },
        ),
        migrations.AddIndex(
            model_name='liquidacionimportacion',
            index=models.Index(fields=['empresa', 'estado'], name='compras_liq_empresa_m4n5o6_idx'),
        ),
        migrations.AddIndex(
            model_name='liquidacionimportacion',
            index=models.Index(fields=['compra', 'estado'], name='compras_liq_compra_p7q8r9_idx'),
        ),
        migrations.AddIndex(
            model_name='liquidacionimportacion',
            index=models.Index(fields=['empresa', 'fecha'], name='compras_liq_empresa_s1t2u3_idx'),
        ),

        # GastoImportacion
        migrations.CreateModel(
            name='GastoImportacion',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('tipo', models.CharField(choices=[('FLETE', 'Flete Internacional'), ('SEGURO', 'Seguro de Carga'), ('ADUANA', 'Gastos de Aduana'), ('IMPUESTOS', 'Impuestos de Importación'), ('TRANSPORTE', 'Transporte Local'), ('ALMACENAJE', 'Almacenaje'), ('AGENTE', 'Comisión Agente Aduanal'), ('OTROS', 'Otros Gastos')], max_length=20)),
                ('descripcion', models.CharField(max_length=255)),
                ('monto', models.DecimalField(decimal_places=2, max_digits=14)),
                ('numero_factura', models.CharField(blank=True, max_length=50, null=True)),
                ('liquidacion', models.ForeignKey(db_index=True, on_delete=django.db.models.deletion.CASCADE, related_name='gastos', to='compras.liquidacionimportacion')),
                ('proveedor_gasto', models.ForeignKey(blank=True, help_text='Proveedor del servicio (naviera, agente, etc.)', null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='gastos_importacion', to='proveedores.proveedor')),
            ],
            options={
                'verbose_name': 'Gasto de Importación',
                'verbose_name_plural': 'Gastos de Importación',
            },
        ),
        migrations.AddIndex(
            model_name='gastoimportacion',
            index=models.Index(fields=['liquidacion', 'tipo'], name='compras_gas_liquida_v4w5x6_idx'),
        ),
    ]
