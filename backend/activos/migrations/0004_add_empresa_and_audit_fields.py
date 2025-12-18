# Manual migration for Activos - Add empresa FK and audit fields
from django.db import migrations, models
from django.conf import settings
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('empresas', '0002_alter_empresa_activo_alter_empresa_rnc_and_more'),
        ('activos', '0003_initial'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        # TipoActivo - Add empresa FK and audit fields
        migrations.AddField(
            model_name='tipoactivo',
            name='empresa',
            field=models.ForeignKey(
                blank=True,
                db_index=True,
                null=True,
                on_delete=django.db.models.deletion.PROTECT,
                related_name='tipos_activo',
                to='empresas.empresa'
            ),
        ),
        migrations.AddField(
            model_name='tipoactivo',
            name='activo',
            field=models.BooleanField(default=True),
        ),
        migrations.AddField(
            model_name='tipoactivo',
            name='fecha_creacion',
            field=models.DateTimeField(auto_now_add=True, null=True),
        ),
        migrations.AddField(
            model_name='tipoactivo',
            name='fecha_actualizacion',
            field=models.DateTimeField(auto_now=True, null=True),
        ),
        migrations.AlterUniqueTogether(
            name='tipoactivo',
            unique_together={('empresa', 'nombre')},
        ),
        migrations.AlterModelOptions(
            name='tipoactivo',
            options={'ordering': ['nombre'], 'verbose_name': 'Tipo de Activo', 'verbose_name_plural': 'Tipos de Activo'},
        ),

        # ActivoFijo - Add empresa FK and audit fields
        migrations.AddField(
            model_name='activofijo',
            name='empresa',
            field=models.ForeignKey(
                blank=True,
                db_index=True,
                null=True,
                on_delete=django.db.models.deletion.PROTECT,
                related_name='activos_fijos',
                to='empresas.empresa'
            ),
        ),
        migrations.AddField(
            model_name='activofijo',
            name='usuario_creacion',
            field=models.ForeignKey(
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name='activos_creados',
                to=settings.AUTH_USER_MODEL
            ),
        ),
        migrations.AddField(
            model_name='activofijo',
            name='usuario_modificacion',
            field=models.ForeignKey(
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name='activos_modificados',
                to=settings.AUTH_USER_MODEL
            ),
        ),
        # Remove unique=True from codigo_interno and add unique_together with empresa
        migrations.AlterField(
            model_name='activofijo',
            name='codigo_interno',
            field=models.CharField(
                help_text='Codigo de etiqueta / Placa de inventario',
                max_length=50
            ),
        ),
        migrations.AlterField(
            model_name='activofijo',
            name='estado',
            field=models.CharField(
                choices=[
                    ('ACTIVO', 'Activo / En Uso'),
                    ('MANTENIMIENTO', 'En Mantenimiento'),
                    ('DEPRECIADO', 'Totalmente Depreciado'),
                    ('VENDIDO', 'Vendido'),
                    ('DESINCORPORADO', 'Desincorporado / Danado')
                ],
                db_index=True,
                default='ACTIVO',
                max_length=20
            ),
        ),
        migrations.AlterUniqueTogether(
            name='activofijo',
            unique_together={('empresa', 'codigo_interno')},
        ),
        migrations.AlterModelOptions(
            name='activofijo',
            options={
                'ordering': ['-fecha_creacion'],
                'verbose_name': 'Activo Fijo',
                'verbose_name_plural': 'Activos Fijos'
            },
        ),

        # Depreciacion - Add audit fields
        migrations.AddField(
            model_name='depreciacion',
            name='fecha_creacion',
            field=models.DateTimeField(auto_now_add=True, null=True),
        ),
        migrations.AddField(
            model_name='depreciacion',
            name='usuario_creacion',
            field=models.ForeignKey(
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name='depreciaciones_creadas',
                to=settings.AUTH_USER_MODEL
            ),
        ),
        migrations.AlterField(
            model_name='depreciacion',
            name='fecha',
            field=models.DateField(db_index=True),
        ),
        migrations.AlterUniqueTogether(
            name='depreciacion',
            unique_together={('activo', 'fecha')},
        ),
        migrations.AlterModelOptions(
            name='depreciacion',
            options={
                'ordering': ['-fecha'],
                'verbose_name': 'Depreciacion',
                'verbose_name_plural': 'Depreciaciones'
            },
        ),
    ]
