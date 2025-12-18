# Generated migration to add empresa FK and timestamp fields

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('empresas', '0001_initial'),
        ('ventas', '0001_initial'),
    ]

    operations = [
        # Add empresa to CotizacionCliente
        migrations.AddField(
            model_name='cotizacioncliente',
            name='empresa',
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.PROTECT,
                related_name='cotizaciones',
                to='empresas.empresa'
            ),
        ),
        migrations.AddField(
            model_name='cotizacioncliente',
            name='fecha_creacion',
            field=models.DateTimeField(auto_now_add=True, null=True, blank=True),
        ),
        migrations.AddField(
            model_name='cotizacioncliente',
            name='fecha_actualizacion',
            field=models.DateTimeField(auto_now=True, null=True, blank=True),
        ),

        # Add empresa to ListaEsperaProducto
        migrations.AddField(
            model_name='listaesperaproducto',
            name='empresa',
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.PROTECT,
                related_name='listas_espera',
                to='empresas.empresa'
            ),
        ),

        # Add empresa to Factura
        migrations.AddField(
            model_name='factura',
            name='empresa',
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.PROTECT,
                related_name='facturas',
                to='empresas.empresa'
            ),
        ),
        migrations.AddField(
            model_name='factura',
            name='fecha_creacion',
            field=models.DateTimeField(auto_now_add=True, null=True, blank=True),
        ),
        migrations.AddField(
            model_name='factura',
            name='fecha_actualizacion',
            field=models.DateTimeField(auto_now=True, null=True, blank=True),
        ),

        # Add empresa to PagoCaja
        migrations.AddField(
            model_name='pagocaja',
            name='empresa',
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.PROTECT,
                related_name='pagos_caja',
                to='empresas.empresa'
            ),
        ),

        # Add empresa to NotaCredito
        migrations.AddField(
            model_name='notacredito',
            name='empresa',
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.PROTECT,
                related_name='notas_credito',
                to='empresas.empresa'
            ),
        ),
        migrations.AddField(
            model_name='notacredito',
            name='fecha_creacion',
            field=models.DateTimeField(auto_now_add=True, null=True, blank=True),
        ),
        migrations.AddField(
            model_name='notacredito',
            name='fecha_actualizacion',
            field=models.DateTimeField(auto_now=True, null=True, blank=True),
        ),

        # Add empresa to NotaDebito
        migrations.AddField(
            model_name='notadebito',
            name='empresa',
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.PROTECT,
                related_name='notas_debito',
                to='empresas.empresa'
            ),
        ),
        migrations.AddField(
            model_name='notadebito',
            name='fecha_creacion',
            field=models.DateTimeField(auto_now_add=True, null=True, blank=True),
        ),
        migrations.AddField(
            model_name='notadebito',
            name='fecha_actualizacion',
            field=models.DateTimeField(auto_now=True, null=True, blank=True),
        ),

        # Add empresa to DevolucionVenta
        migrations.AddField(
            model_name='devolucionventa',
            name='empresa',
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.PROTECT,
                related_name='devoluciones_venta',
                to='empresas.empresa'
            ),
        ),
        migrations.AddField(
            model_name='devolucionventa',
            name='fecha_creacion',
            field=models.DateTimeField(auto_now_add=True, null=True, blank=True),
        ),
        migrations.AddField(
            model_name='devolucionventa',
            name='fecha_actualizacion',
            field=models.DateTimeField(auto_now=True, null=True, blank=True),
        ),

        # Add indexes
        migrations.AddIndex(
            model_name='cotizacioncliente',
            index=models.Index(fields=['empresa', 'estado'], name='ventas_coti_empresa_idx'),
        ),
        migrations.AddIndex(
            model_name='cotizacioncliente',
            index=models.Index(fields=['cliente', 'estado'], name='ventas_coti_cliente_idx'),
        ),
        migrations.AddIndex(
            model_name='cotizacioncliente',
            index=models.Index(fields=['-fecha'], name='ventas_coti_fecha_idx'),
        ),
        migrations.AddIndex(
            model_name='factura',
            index=models.Index(fields=['empresa', 'estado'], name='ventas_fact_empresa_idx'),
        ),
        migrations.AddIndex(
            model_name='factura',
            index=models.Index(fields=['cliente', 'estado'], name='ventas_fact_cliente_idx'),
        ),
        migrations.AddIndex(
            model_name='factura',
            index=models.Index(fields=['empresa', 'fecha'], name='ventas_fact_emp_fecha_idx'),
        ),
        migrations.AddIndex(
            model_name='factura',
            index=models.Index(fields=['numero_factura'], name='ventas_fact_num_idx'),
        ),
        migrations.AddIndex(
            model_name='pagocaja',
            index=models.Index(fields=['empresa', 'fecha_pago'], name='ventas_pago_empresa_idx'),
        ),
        migrations.AddIndex(
            model_name='pagocaja',
            index=models.Index(fields=['cliente', 'fecha_pago'], name='ventas_pago_cliente_idx'),
        ),
        migrations.AddIndex(
            model_name='pagocaja',
            index=models.Index(fields=['metodo_pago', '-fecha_pago'], name='ventas_pago_metodo_idx'),
        ),
    ]
