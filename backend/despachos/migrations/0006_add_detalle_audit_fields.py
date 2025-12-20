# Generated manually for adding audit fields to DetalleDespacho

import uuid
from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion
import django.utils.timezone


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('despachos', '0005_alter_fields'),
    ]

    operations = [
        # Add uuid field
        migrations.AddField(
            model_name='detalledespacho',
            name='uuid',
            field=models.UUIDField(default=uuid.uuid4, editable=False, unique=True),
        ),
        # Add fecha_creacion field (without auto_now_add first)
        migrations.AddField(
            model_name='detalledespacho',
            name='fecha_creacion',
            field=models.DateTimeField(default=django.utils.timezone.now),
            preserve_default=False,
        ),
        # Add fecha_actualizacion field
        migrations.AddField(
            model_name='detalledespacho',
            name='fecha_actualizacion',
            field=models.DateTimeField(auto_now=True),
        ),
        # Add usuario_creacion field
        migrations.AddField(
            model_name='detalledespacho',
            name='usuario_creacion',
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name='detalles_despacho_creados',
                to=settings.AUTH_USER_MODEL
            ),
        ),
        # Add usuario_modificacion field
        migrations.AddField(
            model_name='detalledespacho',
            name='usuario_modificacion',
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name='detalles_despacho_modificados',
                to=settings.AUTH_USER_MODEL
            ),
        ),
        # Update fecha_creacion to have auto_now_add
        migrations.AlterField(
            model_name='detalledespacho',
            name='fecha_creacion',
            field=models.DateTimeField(auto_now_add=True),
        ),
        # Add unique_together constraint
        migrations.AlterUniqueTogether(
            name='detalledespacho',
            unique_together={('despacho', 'producto')},
        ),
        # Add index
        migrations.AddIndex(
            model_name='detalledespacho',
            index=models.Index(fields=['despacho', 'producto'], name='despachos_d_despach_8e79f5_idx'),
        ),
    ]
