"""
Migration for ImagenProducto and ReferenciasCruzadas models.
"""
from django.db import migrations, models
import django.db.models.deletion
import uuid
import productos.models


class Migration(migrations.Migration):

    dependencies = [
        ('productos', '0002_alter_categoria_activa_alter_producto_activo_and_more'),
    ]

    operations = [
        # ImagenProducto model
        migrations.CreateModel(
            name='ImagenProducto',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('imagen', models.ImageField(
                    help_text='Imagen del producto (JPG, PNG, WebP recomendado)',
                    upload_to=productos.models.producto_imagen_path
                )),
                ('titulo', models.CharField(
                    blank=True,
                    help_text='Título o nombre descriptivo de la imagen',
                    max_length=100,
                    null=True
                )),
                ('descripcion', models.TextField(
                    blank=True,
                    help_text='Descripción alternativa (alt text) para accesibilidad',
                    null=True
                )),
                ('es_principal', models.BooleanField(
                    db_index=True,
                    default=False,
                    help_text='Marcar como imagen principal del producto'
                )),
                ('orden', models.PositiveIntegerField(
                    default=0,
                    help_text='Orden de visualización (menor = primero)'
                )),
                ('activa', models.BooleanField(
                    db_index=True,
                    default=True,
                    help_text='Si está activa se muestra en el catálogo'
                )),
                ('uuid', models.UUIDField(default=uuid.uuid4, editable=False, unique=True)),
                ('fecha_creacion', models.DateTimeField(auto_now_add=True)),
                ('fecha_actualizacion', models.DateTimeField(auto_now=True)),
                ('producto', models.ForeignKey(
                    db_index=True,
                    on_delete=django.db.models.deletion.CASCADE,
                    related_name='imagenes',
                    to='productos.producto'
                )),
            ],
            options={
                'verbose_name': 'Imagen de Producto',
                'verbose_name_plural': 'Imágenes de Productos',
                'ordering': ['producto', 'orden', '-es_principal'],
            },
        ),
        # ReferenciasCruzadas model
        migrations.CreateModel(
            name='ReferenciasCruzadas',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('tipo', models.CharField(
                    choices=[
                        ('RELACIONADO', 'Producto Relacionado'),
                        ('SUSTITUTO', 'Producto Sustituto'),
                        ('COMPLEMENTARIO', 'Producto Complementario'),
                        ('ACCESORIO', 'Accesorio'),
                        ('REPUESTO', 'Repuesto')
                    ],
                    db_index=True,
                    default='RELACIONADO',
                    max_length=20
                )),
                ('bidireccional', models.BooleanField(
                    default=True,
                    help_text='Si es True, la relación aplica en ambas direcciones'
                )),
                ('activa', models.BooleanField(db_index=True, default=True)),
                ('uuid', models.UUIDField(default=uuid.uuid4, editable=False, unique=True)),
                ('fecha_creacion', models.DateTimeField(auto_now_add=True)),
                ('producto_origen', models.ForeignKey(
                    db_index=True,
                    on_delete=django.db.models.deletion.CASCADE,
                    related_name='referencias_desde',
                    to='productos.producto'
                )),
                ('producto_destino', models.ForeignKey(
                    db_index=True,
                    on_delete=django.db.models.deletion.CASCADE,
                    related_name='referencias_hacia',
                    to='productos.producto'
                )),
            ],
            options={
                'verbose_name': 'Referencia Cruzada',
                'verbose_name_plural': 'Referencias Cruzadas',
                'ordering': ['producto_origen', 'tipo'],
                'unique_together': {('producto_origen', 'producto_destino', 'tipo')},
            },
        ),
        # Indexes for ImagenProducto
        migrations.AddIndex(
            model_name='imagenproducto',
            index=models.Index(fields=['producto', 'es_principal'], name='productos_i_product_8f3a2c_idx'),
        ),
        migrations.AddIndex(
            model_name='imagenproducto',
            index=models.Index(fields=['producto', 'activa', 'orden'], name='productos_i_product_d7b4e1_idx'),
        ),
    ]
