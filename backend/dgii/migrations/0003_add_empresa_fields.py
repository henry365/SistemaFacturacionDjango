# Manual migration for DGII - Add empresa FK and audit fields
import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('empresas', '0002_alter_empresa_activo_alter_empresa_rnc_and_more'),
        ('dgii', '0002_initial'),
    ]

    operations = [
        # Add empresa FK to TipoComprobante
        migrations.AddField(
            model_name='tipocomprobante',
            name='empresa',
            field=models.ForeignKey(
                blank=True,
                db_index=True,
                null=True,
                on_delete=django.db.models.deletion.PROTECT,
                related_name='tipos_comprobante',
                to='empresas.empresa'
            ),
        ),
        # Add audit fields to TipoComprobante
        migrations.AddField(
            model_name='tipocomprobante',
            name='fecha_creacion',
            field=models.DateTimeField(auto_now_add=True, null=True),
        ),
        migrations.AddField(
            model_name='tipocomprobante',
            name='fecha_actualizacion',
            field=models.DateTimeField(auto_now=True, null=True),
        ),
        # Remove unique constraint on codigo (will be unique per empresa)
        migrations.AlterField(
            model_name='tipocomprobante',
            name='codigo',
            field=models.CharField(help_text='Ej: 01, 02, 11, 14, 15', max_length=2),
        ),
        # Add empresa FK to SecuenciaNCF
        migrations.AddField(
            model_name='secuenciancf',
            name='empresa',
            field=models.ForeignKey(
                blank=True,
                db_index=True,
                null=True,
                on_delete=django.db.models.deletion.PROTECT,
                related_name='secuencias_ncf',
                to='empresas.empresa'
            ),
        ),
        # Update tipo_comprobante related_name
        migrations.AlterField(
            model_name='secuenciancf',
            name='tipo_comprobante',
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.PROTECT,
                related_name='secuencias',
                to='dgii.tipocomprobante'
            ),
        ),
        # Update unique_together for TipoComprobante
        migrations.AlterUniqueTogether(
            name='tipocomprobante',
            unique_together={('empresa', 'codigo')},
        ),
        # Update unique_together for SecuenciaNCF
        migrations.AlterUniqueTogether(
            name='secuenciancf',
            unique_together={('empresa', 'tipo_comprobante', 'secuencia_inicial')},
        ),
    ]
