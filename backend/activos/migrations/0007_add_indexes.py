# Migration for adding indexes to activos models
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('activos', '0006_activofijo_depreciacion_acumulada'),
    ]

    operations = [
        # Add index to fecha_adquisicion in ActivoFijo
        migrations.AlterField(
            model_name='activofijo',
            name='fecha_adquisicion',
            field=models.DateField(db_index=True),
        ),
        # Add composite index to Depreciacion (activo, fecha)
        migrations.AddIndex(
            model_name='depreciacion',
            index=models.Index(
                fields=['activo', 'fecha'],
                name='activos_dep_activo_fecha_idx'
            ),
        ),
    ]
