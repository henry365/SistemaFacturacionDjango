"""
Migration for TipoRetencion and RetencionCompra models.
"""
from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion
import uuid


class Migration(migrations.Migration):

    dependencies = [
        ('compras', '0006_add_recepcion_devolucion_liquidacion'),
        ('empresas', '0002_alter_empresa_activo_alter_empresa_rnc_and_more'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        # TipoRetencion model
        migrations.CreateModel(
            name='TipoRetencion',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('codigo', models.CharField(help_text='Código DGII (ej: 01, 02)', max_length=10)),
                ('nombre', models.CharField(help_text='Ej: ISR Personas Físicas, ITBIS 30%', max_length=100)),
                ('categoria', models.CharField(
                    choices=[('ISR', 'Impuesto Sobre la Renta'), ('ITBIS', 'ITBIS Retenido')],
                    db_index=True,
                    max_length=10
                )),
                ('porcentaje', models.DecimalField(
                    decimal_places=2,
                    help_text='Porcentaje de retención (ej: 10.00 para 10%)',
                    max_digits=5
                )),
                ('aplica_a_persona_fisica', models.BooleanField(
                    default=False,
                    help_text='Si aplica automáticamente a proveedores persona física'
                )),
                ('aplica_a_persona_juridica', models.BooleanField(
                    default=False,
                    help_text='Si aplica automáticamente a proveedores persona jurídica'
                )),
                ('activo', models.BooleanField(default=True)),
                ('uuid', models.UUIDField(default=uuid.uuid4, editable=False, unique=True)),
                ('fecha_creacion', models.DateTimeField(auto_now_add=True)),
                ('fecha_actualizacion', models.DateTimeField(auto_now=True)),
                ('empresa', models.ForeignKey(
                    blank=True,
                    db_index=True,
                    null=True,
                    on_delete=django.db.models.deletion.PROTECT,
                    related_name='tipos_retencion',
                    to='empresas.empresa'
                )),
            ],
            options={
                'verbose_name': 'Tipo de Retención',
                'verbose_name_plural': 'Tipos de Retención',
                'ordering': ['categoria', 'codigo'],
                'unique_together': {('empresa', 'codigo')},
            },
        ),
        # RetencionCompra model
        migrations.CreateModel(
            name='RetencionCompra',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('base_imponible', models.DecimalField(
                    decimal_places=2,
                    help_text='Monto sobre el cual se calcula la retención',
                    max_digits=14
                )),
                ('porcentaje', models.DecimalField(
                    decimal_places=2,
                    help_text='Porcentaje aplicado (copia del tipo al momento de aplicar)',
                    max_digits=5
                )),
                ('monto_retenido', models.DecimalField(
                    decimal_places=2,
                    help_text='Monto de la retención',
                    max_digits=14
                )),
                ('fecha_aplicacion', models.DateField(auto_now_add=True)),
                ('observaciones', models.TextField(blank=True, null=True)),
                ('uuid', models.UUIDField(default=uuid.uuid4, editable=False, unique=True)),
                ('fecha_creacion', models.DateTimeField(auto_now_add=True)),
                ('fecha_actualizacion', models.DateTimeField(auto_now=True)),
                ('empresa', models.ForeignKey(
                    blank=True,
                    db_index=True,
                    null=True,
                    on_delete=django.db.models.deletion.PROTECT,
                    related_name='retenciones_compra',
                    to='empresas.empresa'
                )),
                ('compra', models.ForeignKey(
                    db_index=True,
                    on_delete=django.db.models.deletion.CASCADE,
                    related_name='retenciones',
                    to='compras.compra'
                )),
                ('tipo_retencion', models.ForeignKey(
                    on_delete=django.db.models.deletion.PROTECT,
                    related_name='retenciones_aplicadas',
                    to='compras.tiporetencion'
                )),
                ('usuario_creacion', models.ForeignKey(
                    blank=True,
                    null=True,
                    on_delete=django.db.models.deletion.SET_NULL,
                    related_name='retenciones_creadas',
                    to=settings.AUTH_USER_MODEL
                )),
            ],
            options={
                'verbose_name': 'Retención en Compra',
                'verbose_name_plural': 'Retenciones en Compras',
                'ordering': ['-fecha_creacion'],
            },
        ),
        # Indexes for RetencionCompra
        migrations.AddIndex(
            model_name='retencioncompra',
            index=models.Index(fields=['empresa', 'compra'], name='compras_ret_empresa_d8b3f5_idx'),
        ),
        migrations.AddIndex(
            model_name='retencioncompra',
            index=models.Index(fields=['tipo_retencion', 'fecha_aplicacion'], name='compras_ret_tipo_re_a1c4f2_idx'),
        ),
    ]
