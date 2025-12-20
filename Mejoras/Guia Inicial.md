# Guía Inicial - Estándares y Mejores Prácticas para Módulos

**Fecha:** 2025-01-27  
**Versión:** 1.0  
**Basado en:** Módulo Activos Fijos (referencia de implementación)  
**Django:** 6.0  
**Estado:** Activo

---

## 🎯 Principios de Diseño

Este proyecto sigue estrictamente los siguientes principios de diseño de software:

### DRY (Don't Repeat Yourself)
**No repetir código.** Toda lógica común debe estar centralizada y reutilizable.
- ✅ Usar clases base genéricas (`core.permissions.BaseEmpresaPermission`)
- ✅ Usar mixins reutilizables (`core.permissions.mixins`)
- ✅ Crear servicios para lógica de negocio compartida
- ✅ Centralizar constantes en `constants.py`
- ❌ NO duplicar código de verificación de permisos
- ❌ NO repetir validaciones en múltiples lugares

### KISS (Keep It Simple, Stupid)
**Mantener las cosas simples.** La simplicidad es la máxima sofisticación.
- ✅ Soluciones simples y directas
- ✅ Código fácil de entender sin documentación excesiva
- ✅ Evitar sobre-ingeniería
- ❌ NO crear abstracciones innecesarias
- ❌ NO agregar complejidad "por si acaso"

### SRP (Single Responsibility Principle)
**Cada clase/módulo tiene una sola responsabilidad.**
- ✅ Modelos solo manejan datos y validaciones básicas
- ✅ Servicios manejan lógica de negocio
- ✅ Vistas manejan requests/responses
- ✅ Serializers manejan serialización/validación de entrada
- ❌ NO mezclar responsabilidades (ej: lógica de negocio en modelos)
- ❌ NO hacer clases que hagan "todo"

### SoC (Separation of Concerns)
**Separar preocupaciones en capas distintas.**
- ✅ Separar lógica de negocio (`services.py`) de presentación (`views.py`)
- ✅ Separar validaciones de modelos (`clean()`) de validaciones de entrada (`serializers`)
- ✅ Separar permisos (`permissions.py`) de lógica de negocio
- ✅ Separar constantes (`constants.py`) de código
- ❌ NO mezclar capas (ej: queries complejas en vistas)
- ❌ NO poner lógica de negocio en modelos o vistas

### YAGNI (You Aren't Gonna Need It)
**No implementar funcionalidad hasta que sea necesaria.**
- ✅ Implementar solo lo que se necesita ahora
- ✅ Evitar funcionalidad "por si acaso"
- ✅ Refactorizar cuando realmente se necesite
- ❌ NO crear abstracciones "por si en el futuro..."
- ❌ NO agregar campos "por si acaso se necesitan"

### ⚠️ IDEMPOTENCIA (OBLIGATORIO)
**Las operaciones deben poder ejecutarse múltiples veces sin cambiar el resultado más allá de la primera ejecución.**

**La idempotencia es OBLIGATORIA para:**
- ✅ Operaciones HTTP (PUT, DELETE, PATCH deben ser idempotentes)
- ✅ Endpoints de acciones personalizadas (`@action`)
- ✅ Servicios que modifican datos
- ✅ Migraciones de base de datos
- ✅ Operaciones de actualización de estado
- ✅ Operaciones que pueden recibir requests duplicados

**Cómo garantizar idempotencia:**
- ✅ Usar identificadores únicos (UUID, códigos) para verificar si la operación ya se realizó
- ✅ Verificar estado antes de modificar (ej: "ya está en este estado, no hacer nada")
- ✅ Usar transacciones atómicas para operaciones múltiples
- ✅ Retornar el mismo resultado si se ejecuta múltiples veces
- ✅ No crear registros duplicados (verificar existencia antes de crear)
- ✅ No aplicar cambios si ya están aplicados (verificar estado actual)

**Ejemplos de idempotencia:**
- ✅ PUT `/api/v1/activos/{id}/` con los mismos datos → mismo resultado siempre
- ✅ POST `/api/v1/activos/{id}/depreciar` con misma fecha → no crear depreciación duplicada
- ✅ Cambiar estado a "DEPRECIADO" múltiples veces → siempre termina en "DEPRECIADO"
- ✅ Migración que agrega campo → puede ejecutarse múltiples veces sin error

**❌ NO HACER:**
- ❌ NO crear operaciones que generen efectos secundarios diferentes en ejecuciones repetidas
- ❌ NO crear registros duplicados si se ejecuta múltiples veces
- ❌ NO modificar datos de forma diferente en cada ejecución
- ❌ NO crear endpoints que dependan del número de veces que se llaman

---

## 📋 Tabla de Contenidos

1. [Principios de Diseño](#-principios-de-diseño)
2. [Estructura de Archivos](#estructura-de-archivos)
3. [Modelos (Models)](#modelos-models)
4. [Migraciones (Migrations)](#migraciones-migrations)
5. [Vistas (Views)](#vistas-views)
6. [Serializers](#serializers)
7. [Permisos (Permissions)](#permisos-permissions)
8. [Servicios (Services)](#servicios-services)
9. [Señales (Signals)](#señales-signals)
10. [Constantes (Constants)](#constantes-constants)
11. [Admin](#admin)
12. [Tests](#tests)
13. [Apps Config](#apps-config)
14. [Checklist de Implementación](#checklist-de-implementación)

---

## Estructura de Archivos

### Estructura Estándar Recomendada

```
backend/[nombre_modulo]/
├── __init__.py
├── admin.py              # Configuración del admin de Django
├── apps.py               # Configuración de la app (registro de señales)
├── constants.py          # Constantes del módulo (opcional pero recomendado)
├── models.py             # Modelos de datos
├── permissions.py        # Permisos personalizados (usando core.permissions)
├── serializers.py        # Serializers de DRF
├── services.py           # Lógica de negocio separada (opcional pero recomendado)
├── signals.py            # Señales de Django (opcional)
├── tests.py              # Tests unitarios e integración
├── urls.py               # URLs del módulo
├── views.py              # ViewSets y vistas de DRF
└── migrations/           # Migraciones de base de datos
    ├── __init__.py
    └── 0001_initial.py
```

### Archivos Opcionales pero Recomendados

- `constants.py` - Para centralizar constantes (estados, valores por defecto, etc.)
- `services.py` - Para separar lógica de negocio de las vistas
- `signals.py` - Para automatizar comportamientos del sistema

---

## Modelos (Models)

### ⚠️ CRÍTICO: Integridad de Datos es Prioridad Absoluta

**La integridad de los datos es la responsabilidad más importante de los modelos.**

**Los modelos deben:**
- ✅ **Validar TODOS los datos** antes de guardar (`clean()`)
- ✅ **Garantizar consistencia** de datos en todo momento
- ✅ **Prevenir datos inválidos** desde el origen
- ✅ **Proteger relaciones** con `on_delete` apropiado
- ✅ **Usar constraints de base de datos** cuando sea necesario
- ✅ **Validar reglas de negocio** antes de persistir

**Errores en validaciones pueden:**
- Corromper datos en producción
- Causar inconsistencias en la base de datos
- Generar errores en cascada
- Perder información crítica
- Violar reglas de negocio

**SIEMPRE implementar validaciones completas en `clean()`**

### Estructura Básica de un Modelo

```python
"""
Modelos para [Nombre del Módulo]

Django 6.0: Usa características modernas de Django
"""
from decimal import Decimal
from django.db import models, transaction
from django.db.models import F, GeneratedField  # Si necesitas campos calculados
from django.conf import settings
from django.core.exceptions import ValidationError
from django.utils import timezone
import uuid


class MiModelo(models.Model):
    """
    Descripción del modelo.
    
    Campos principales y propósito del modelo.
    """
    
    # Campo de empresa (OBLIGATORIO para multi-tenancy)
    empresa = models.ForeignKey(
        'empresas.Empresa',
        on_delete=models.PROTECT,
        related_name='[nombre_relacion]',
        db_index=True,  # Siempre indexar empresa
        null=True,
        blank=True
    )
    
    # Campos de identificación
    nombre = models.CharField(max_length=200)
    codigo = models.CharField(max_length=50, unique=True)
    
    # Campos de auditoría (OBLIGATORIOS)
    uuid = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)
    fecha_creacion = models.DateTimeField(auto_now_add=True)
    fecha_actualizacion = models.DateTimeField(auto_now=True)
    usuario_creacion = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='[modelo]_creados'
    )
    usuario_modificacion = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='[modelo]_modificados'
    )
    
    class Meta:
        verbose_name = 'Mi Modelo'
        verbose_name_plural = 'Mis Modelos'
        unique_together = ('empresa', 'codigo')  # Si aplica
        ordering = ['-fecha_creacion']  # Orden por defecto
        indexes = [
            models.Index(fields=['empresa', 'fecha_creacion']),  # Índices compuestos si es necesario
        ]
        # Permisos personalizados si es necesario
        permissions = [
            ('accion_modelo', 'Puede realizar acción específica'),
        ]
    
    def __str__(self):
        return f"{self.codigo} - {self.nombre}"
    
    def clean(self):
        """
        Validaciones de negocio para MiModelo.
        
        ⚠️ CRÍTICO: Este método es OBLIGATORIO y debe validar TODAS las reglas de negocio.
        La integridad de los datos depende de estas validaciones.
        
        Siempre implementar validaciones de negocio aquí.
        """
        errors = {}
        
        # ========== VALIDACIONES DE VALORES ==========
        
        # Validar valores no negativos
        if hasattr(self, 'valor') and self.valor is not None:
            if self.valor < 0:
                errors['valor'] = 'El valor no puede ser negativo'
        
        # Validar rangos de valores
        if hasattr(self, 'porcentaje') and self.porcentaje is not None:
            if self.porcentaje < 0 or self.porcentaje > 100:
                errors['porcentaje'] = 'El porcentaje debe estar entre 0 y 100'
        
        # ========== VALIDACIONES DE FECHAS ==========
        
        # Validar fechas no futuras
        if hasattr(self, 'fecha') and self.fecha is not None:
            if self.fecha > timezone.now().date():
                errors['fecha'] = 'La fecha no puede ser futura'
        
        # Validar consistencia de fechas
        if (hasattr(self, 'fecha_inicio') and hasattr(self, 'fecha_fin') and
            self.fecha_inicio is not None and self.fecha_fin is not None):
            if self.fecha_fin < self.fecha_inicio:
                errors['fecha_fin'] = 'La fecha fin no puede ser anterior a la fecha inicio'
        
        # ========== VALIDACIONES DE RELACIONES ==========
        
        # Validar relaciones de empresa (CRÍTICO para multi-tenancy)
        if (self.empresa is not None and 
            hasattr(self, 'relacion') and 
            self.relacion is not None and
            hasattr(self.relacion, 'empresa')):
            if self.relacion.empresa != self.empresa:
                errors['relacion'] = 'La relación debe pertenecer a la misma empresa'
        
        # Validar que relaciones requeridas existan
        if hasattr(self, 'relacion_requerida') and self.relacion_requerida is None:
            errors['relacion_requerida'] = 'La relación requerida es obligatoria'
        
        # ========== VALIDACIONES DE CONSISTENCIA ==========
        
        # Validar que campo1 <= campo2
        if (hasattr(self, 'campo1') and hasattr(self, 'campo2') and
            self.campo1 is not None and self.campo2 is not None):
            if self.campo1 > self.campo2:
                errors['campo1'] = 'Campo1 no puede ser mayor que Campo2'
        
        # Validar suma de campos
        if (hasattr(self, 'subtotal') and hasattr(self, 'total') and
            self.subtotal is not None and self.total is not None):
            if self.subtotal > self.total:
                errors['subtotal'] = 'El subtotal no puede ser mayor que el total'
        
        # ========== VALIDACIONES DE ESTADO ==========
        
        # Validar transiciones de estado si aplica
        if hasattr(self, 'estado') and self.pk:  # Solo en updates
            estado_anterior = type(self).objects.get(pk=self.pk).estado
            if not self._es_transicion_valida(estado_anterior, self.estado):
                errors['estado'] = f'No se puede cambiar de {estado_anterior} a {self.estado}'
        
        # ========== VALIDACIONES DE UNICIDAD ==========
        
        # Validar unicidad personalizada (si no se puede hacer con unique_together)
        if hasattr(self, 'codigo') and self.codigo:
            qs = type(self).objects.filter(codigo=self.codigo, empresa=self.empresa)
            if self.pk:
                qs = qs.exclude(pk=self.pk)
            if qs.exists():
                errors['codigo'] = 'Ya existe un registro con este código para esta empresa'
        
        # ========== LANZAR ERRORES ==========
        
        if errors:
            raise ValidationError(errors)
    
    def _es_transicion_valida(self, estado_anterior, estado_nuevo):
        """
        Valida si una transición de estado es válida.
        
        Returns:
            bool: True si la transición es válida
        """
        # Definir transiciones permitidas
        transiciones_permitidas = {
            'ESTADO1': ['ESTADO2', 'ESTADO3'],
            'ESTADO2': ['ESTADO3', 'ESTADO_FINAL'],
        }
        
        estados_permitidos = transiciones_permitidas.get(estado_anterior, [])
        return estado_nuevo in estados_permitidos or estado_anterior == estado_nuevo
    
    def save(self, *args, **kwargs):
        """
        Guarda el modelo con validaciones.
        
        ⚠️ CRÍTICO: Siempre ejecutar validaciones antes de guardar.
        La integridad de los datos depende de esto.
        
        Nota: Solo omitir full_clean si es update_fields y estamos seguros
        de que los campos actualizados no requieren validación completa.
        """
        # Ejecutar validaciones completas antes de guardar
        # Solo omitir si es update_fields y estamos seguros de la integridad
        if 'update_fields' not in kwargs:
            self.full_clean()  # Validar TODO
        else:
            # Incluso con update_fields, validar si es crítico
            # O al menos validar los campos que se están actualizando
            update_fields = kwargs.get('update_fields', [])
            # Si se actualizan campos críticos, validar completo
            campos_criticos = ['empresa', 'relacion', 'estado', 'valor']
            if any(campo in update_fields for campo in campos_criticos):
                self.full_clean()
        
        super().save(*args, **kwargs)
    
    @property
    def propiedad_calculada(self):
        """
        Propiedades calculadas usando @property.
        
        Returns:
            Valor calculado
        """
        # Lógica de cálculo
        return 0
```

### Mejores Prácticas para Modelos

#### Principios Aplicados:
- **SRP**: Modelos solo manejan datos y validaciones básicas
- **DRY**: Validaciones comunes en `clean()`, no repetir en múltiples lugares
- **KISS**: Validaciones simples y directas
- **SoC**: Separar validaciones de datos de lógica de negocio (que va en servicios)

#### ⚠️ PRIORIDAD ABSOLUTA: Integridad de Datos

**Las validaciones son OBLIGATORIAS y deben ser COMPLETAS:**

1. **SIEMPRE implementar `clean()`** - No es opcional
2. **Validar TODOS los campos** - No dejar campos sin validar
3. **Validar relaciones** - Especialmente empresa (multi-tenancy)
4. **Validar consistencia** - Entre campos relacionados
5. **Validar reglas de negocio** - Antes de persistir
6. **Usar `full_clean()` en `save()`** - Para garantizar validaciones

#### ✅ HACER:

1. **Siempre incluir campo `empresa`** para multi-tenancy
2. **Siempre incluir campos de auditoría** (uuid, fecha_creacion, fecha_actualizacion, usuario_creacion, usuario_modificacion)
3. **Implementar `clean()` COMPLETO** para validaciones de negocio (OBLIGATORIO)
   - Validar valores numéricos (no negativos, rangos)
   - Validar fechas (no futuras, consistencia)
   - Validar relaciones (empresa, integridad referencial)
   - Validar consistencia entre campos
   - Validar reglas de negocio específicas
4. **Usar `full_clean()` en `save()`** para garantizar validaciones siempre
5. **Usar `db_index=True`** en campos frecuentemente consultados (empresa, fechas, estados)
6. **Usar `related_name`** descriptivo en ForeignKeys
7. **Usar `on_delete=models.PROTECT`** para relaciones críticas (protege integridad)
8. **Usar `unique_together`** en Meta para garantizar unicidad
9. **Usar `db_constraints`** en Meta si necesitas constraints de base de datos
10. **Definir `verbose_name` y `verbose_name_plural`** en Meta
11. **Definir `ordering`** por defecto
12. **Usar `GeneratedField`** (Django 6.0) para campos calculados automáticamente (DRY: no calcular manualmente)
13. **Documentar con docstrings** claros
14. **Validar transiciones de estado** si el modelo tiene estados

#### ❌ NO HACER:

1. ❌ **NO crear modelos sin `clean()`** - Es OBLIGATORIO
2. ❌ **NO dejar campos sin validar** - Todos deben tener validación
3. ❌ **NO confiar solo en validaciones de serializers** - Validar también en modelos
4. ❌ **NO poner lógica de negocio compleja en `save()`** (SRP: usar servicios)
5. ❌ **NO hacer queries en propiedades** (YAGNI: solo si realmente se necesita)
6. ❌ **NO usar `null=True` y `blank=True` sin razón válida** (KISS: mantener simple)
7. ❌ **NO olvidar `db_index=True`** en campos de empresa y fechas
8. ❌ **NO usar `on_delete=models.CASCADE`** sin considerar el impacto en integridad
9. ❌ **NO duplicar validaciones** (DRY: centralizar en `clean()`)
10. ❌ **NO agregar campos "por si acaso"** (YAGNI: solo lo necesario)
11. ❌ **NO permitir datos inválidos** - Siempre lanzar ValidationError
12. ❌ **NO saltarse validaciones** - Siempre llamar `full_clean()`

### Ejemplo Real: ActivoFijo (Validaciones Completas)

```python
class ActivoFijo(models.Model):
    """Registro de activos fijos de la empresa"""
    
    empresa = models.ForeignKey(
        'empresas.Empresa',
        on_delete=models.PROTECT,  # Protege integridad referencial
        related_name='activos_fijos',
        db_index=True,
        null=True,
        blank=True
    )
    
    # Django 6.0: Campo calculado automáticamente
    depreciacion_acumulada = GeneratedField(
        expression=F('valor_adquisicion') - F('valor_libro_actual'),
        output_field=models.DecimalField(max_digits=14, decimal_places=2),
        db_persist=True,
        help_text="Depreciación acumulada (calculado automáticamente)"
    )
    
    def clean(self):
        """
        Validaciones de negocio para ActivoFijo.
        
        ⚠️ CRÍTICO: Estas validaciones garantizan la integridad de los datos.
        """
        errors = {}
        
        # ========== VALIDACIONES DE VALORES MONETARIOS ==========
        
        # Validar valores monetarios no negativos
        if self.valor_adquisicion is not None and self.valor_adquisicion < 0:
            errors['valor_adquisicion'] = 'El valor de adquisicion no puede ser negativo'
        
        if self.valor_libro_actual is not None and self.valor_libro_actual < 0:
            errors['valor_libro_actual'] = 'El valor libro no puede ser negativo'
        
        # ========== VALIDACIONES DE CONSISTENCIA ==========
        
        # Validar que valor_libro_actual <= valor_adquisicion
        if (self.valor_adquisicion is not None and
            self.valor_libro_actual is not None and
            self.valor_libro_actual > self.valor_adquisicion):
            errors['valor_libro_actual'] = 'El valor libro no puede ser mayor al valor de adquisicion'
        
        # ========== VALIDACIONES DE FECHAS ==========
        
        # Validar que fecha_adquisicion no sea futura
        if self.fecha_adquisicion is not None and self.fecha_adquisicion > timezone.now().date():
            errors['fecha_adquisicion'] = 'La fecha de adquisicion no puede ser futura'
        
        # ========== VALIDACIONES DE RELACIONES ==========
        
        # Validar que tipo_activo pertenezca a la misma empresa
        if (self.empresa is not None and
            self.tipo_activo is not None and
            self.tipo_activo.empresa is not None and
            self.tipo_activo.empresa != self.empresa):
            errors['tipo_activo'] = 'El tipo de activo debe pertenecer a la misma empresa'
        
        if errors:
            raise ValidationError(errors)
    
    def save(self, *args, **kwargs):
        """
        Guarda con validaciones completas.
        
        ⚠️ CRÍTICO: Siempre validar antes de guardar para garantizar integridad.
        """
        # Solo ejecutar full_clean si no es update_fields
        if 'update_fields' not in kwargs:
            self.full_clean()
        super().save(*args, **kwargs)
```

**Características de este ejemplo:**
- ✅ Validaciones completas de todos los campos críticos
- ✅ Validación de valores monetarios (no negativos)
- ✅ Validación de consistencia entre campos
- ✅ Validación de fechas
- ✅ Validación de relaciones (empresa)
- ✅ `full_clean()` en `save()` para garantizar validaciones
- ✅ `on_delete=models.PROTECT` para proteger integridad referencial

---

## Migraciones (Migrations)

### ⚠️ CRÍTICO: Las Migraciones Deben Estar Correctas

**Las migraciones son código que modifica la base de datos. Errores en migraciones pueden:**
- Corromper datos existentes
- Bloquear despliegues
- Causar pérdida de información
- Romper el sistema en producción

**SIEMPRE verificar que las migraciones:**
- ✅ No tengan errores de sintaxis
- ✅ No tengan errores lógicos
- ✅ Se puedan aplicar correctamente (`python manage.py migrate`)
- ✅ Se puedan revertir correctamente (`python manage.py migrate app_name previous_version`)
- ✅ No causen pérdida de datos
- ✅ Sean compatibles con datos existentes

### Estructura Básica de una Migración

```python
# Generated by Django 6.0 on YYYY-MM-DD HH:MM

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('app_name', 'previous_migration'),
        ('other_app', 'other_migration'),  # Si hay dependencias externas
    ]

    operations = [
        migrations.CreateModel(
            name='MiModelo',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('nombre', models.CharField(max_length=200)),
                ('empresa', models.ForeignKey(
                    on_delete=django.db.models.deletion.PROTECT,
                    to='empresas.Empresa'
                )),
            ],
            options={
                'verbose_name': 'Mi Modelo',
                'verbose_name_plural': 'Mis Modelos',
            },
        ),
    ]
```

### Mejores Prácticas para Migraciones

#### Principios Aplicados:
- **KISS**: Migraciones simples y directas, una cosa a la vez
- **SRP**: Cada migración tiene un propósito específico
- **DRY**: Reutilizar operaciones estándar de Django
- **SoC**: Separar cambios de estructura de cambios de datos
- **IDEMPOTENCIA**: Las migraciones deben ser idempotentes (OBLIGATORIO - Django las hace idempotentes por defecto, pero verificar en RunPython)

#### ✅ HACER:

1. **Verificar sintaxis antes de commitear**
   ```bash
   python manage.py makemigrations --dry-run
   python manage.py migrate --plan
   ```

2. **Probar migraciones en desarrollo antes de producción**
   ```bash
   # Aplicar migración
   python manage.py migrate
   
   # Verificar que no haya errores
   python manage.py check
   
   # Probar revertir (si es necesario)
   python manage.py migrate app_name previous_version
   python manage.py migrate app_name latest_version
   ```

3. **Usar nombres descriptivos** para migraciones personalizadas
   ```python
   # ✅ BUENO
   class Migration(migrations.Migration):
       # Migration for adding indexes to activos models
   
   # ❌ MALO
   class Migration(migrations.Migration):
       # Migration
   ```

4. **Documentar migraciones complejas** con comentarios
   ```python
   operations = [
       # Add index to fecha_adquisicion for performance
       migrations.AlterField(
           model_name='activofijo',
           name='fecha_adquisicion',
           field=models.DateField(db_index=True),
       ),
   ]
   ```

5. **Usar `migrations.RunPython` con cuidado** - solo cuando sea absolutamente necesario
   ```python
   def migrar_datos(apps, schema_editor):
       """Migrar datos existentes"""
       MiModelo = apps.get_model('app', 'MiModelo')
       # Lógica de migración de datos
   
   operations = [
       migrations.RunPython(migrar_datos, migrations.RunPython.noop),
   ]
   ```

6. **Verificar dependencias** - asegurar que todas las dependencias estén correctas
   ```python
   dependencies = [
       ('activos', '0007_add_indexes'),  # ✅ Verificar que existe
       ('empresas', '0001_initial'),    # ✅ Verificar que existe
   ]
   ```

7. **Usar `migrations.SeparateDatabaseAndState`** para cambios complejos que requieren múltiples pasos

8. **Probar con datos reales** antes de aplicar en producción

9. **Garantizar idempotencia** en migraciones personalizadas (IDEMPOTENCIA: obligatorio)
    - Las operaciones estándar de Django son idempotentes por defecto
    - En `RunPython`, verificar estado antes de modificar datos
    - No crear registros duplicados en migraciones de datos
    - Verificar si la migración ya se aplicó antes de ejecutar lógica
    ```python
    def migrar_datos(apps, schema_editor):
        """Migrar datos existentes (idempotente)"""
        MiModelo = apps.get_model('app', 'MiModelo')
        
        # Verificar si ya se migró (idempotencia)
        if MiModelo.objects.filter(campo_nuevo__isnull=False).exists():
            return  # Ya se migró, no hacer nada
        
        # Migrar solo si no se ha migrado antes
        for modelo in MiModelo.objects.filter(campo_nuevo__isnull=True):
            modelo.campo_nuevo = calcular_valor(modelo)
            modelo.save(update_fields=['campo_nuevo'])
    ```

#### ❌ NO HACER:

1. ❌ **NO crear migraciones con errores de sintaxis**
2. ❌ **NO crear migraciones que puedan perder datos** sin migración de datos previa
3. ❌ **NO modificar migraciones ya aplicadas** en producción (crear nueva migración)
4. ❌ **NO usar `migrations.RunPython`** sin función de reversión
5. ❌ **NO olvidar actualizar `dependencies`** cuando hay cambios en otros módulos
6. ❌ **NO crear migraciones que dependan de código que no existe**
7. ❌ **NO aplicar migraciones sin probar primero** en desarrollo
8. ❌ **NO mezclar cambios de estructura con cambios de datos** en la misma migración (si es complejo)

### Verificación de Migraciones

#### Checklist Pre-Commit:

```bash
# 1. Verificar que se pueden crear migraciones sin errores
python manage.py makemigrations --dry-run

# 2. Crear migraciones
python manage.py makemigrations

# 3. Verificar plan de migración
python manage.py migrate --plan

# 4. Aplicar migraciones en desarrollo
python manage.py migrate

# 5. Verificar que no hay errores
python manage.py check

# 6. Probar revertir (si aplica)
python manage.py migrate app_name previous_version
python manage.py migrate app_name latest_version

# 7. Ejecutar tests para verificar que todo funciona
python manage.py test app_name
```

#### Verificación Post-Migración:

1. ✅ Verificar que la migración se aplicó correctamente
   ```bash
   python manage.py showmigrations app_name
   ```

2. ✅ Verificar estructura de base de datos
   ```bash
   python manage.py dbshell
   # Verificar tablas, índices, constraints
   ```

3. ✅ Verificar que los datos están correctos
   ```bash
   python manage.py shell
   # Verificar que los modelos funcionan correctamente
   ```

### Tipos Comunes de Migraciones

#### 1. Migración Inicial (Crear Modelo)

```python
class Migration(migrations.Migration):
    initial = True
    
    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('empresas', '0001_initial'),
    ]
    
    operations = [
        migrations.CreateModel(
            name='MiModelo',
            fields=[...],
        ),
    ]
```

#### 2. Agregar Campo

```python
class Migration(migrations.Migration):
    dependencies = [
        ('app', '0001_initial'),
    ]
    
    operations = [
        migrations.AddField(
            model_name='mimodelo',
            name='nuevo_campo',
            field=models.CharField(max_length=100, null=True, blank=True),
        ),
    ]
```

#### 3. Agregar Índice

```python
class Migration(migrations.Migration):
    dependencies = [
        ('app', '0002_add_field'),
    ]
    
    operations = [
        migrations.AlterField(
            model_name='mimodelo',
            name='campo_frecuente',
            field=models.CharField(max_length=100, db_index=True),
        ),
        migrations.AddIndex(
            model_name='mimodelo',
            index=models.Index(
                fields=['campo1', 'campo2'],
                name='app_mimodelo_campo1_campo2_idx'
            ),
        ),
    ]
```

#### 4. Agregar Permisos Personalizados

```python
class Migration(migrations.Migration):
    dependencies = [
        ('app', '0003_add_index'),
    ]
    
    operations = [
        migrations.AlterModelOptions(
            name='mimodelo',
            options={
                'permissions': [
                    ('accion_modelo', 'Puede realizar acción específica'),
                ],
            },
        ),
    ]
```

#### 5. Migración de Datos (RunPython)

```python
def migrar_datos(apps, schema_editor):
    """Migrar datos existentes a nuevo formato"""
    MiModelo = apps.get_model('app', 'MiModelo')
    
    for modelo in MiModelo.objects.all():
        # Lógica de migración
        modelo.nuevo_campo = calcular_valor(modelo)
        modelo.save(update_fields=['nuevo_campo'])


def revertir_migracion(apps, schema_editor):
    """Revertir migración de datos"""
    # Lógica de reversión si es posible
    pass


class Migration(migrations.Migration):
    dependencies = [
        ('app', '0004_add_field'),
    ]
    
    operations = [
        migrations.RunPython(
            migrar_datos,
            revertir_migracion  # Siempre incluir función de reversión
        ),
    ]
```

### Errores Comunes en Migraciones

#### Error 1: Dependencias Incorrectas

```python
# ❌ MALO - Dependencia que no existe
dependencies = [
    ('app', '0009_no_existe'),  # Error: migración no existe
]

# ✅ BUENO - Verificar dependencias antes
dependencies = [
    ('app', '0008_actual'),  # Verificado que existe
]
```

#### Error 2: Campo que No Existe

```python
# ❌ MALO - Modificar campo que no existe
operations = [
    migrations.AlterField(
        model_name='mimodelo',
        name='campo_inexistente',  # Error: campo no existe
        field=models.CharField(max_length=100),
    ),
]

# ✅ BUENO - Verificar modelo antes de modificar
# Primero agregar el campo, luego modificarlo si es necesario
```

#### Error 3: Migración Irreversible

```python
# ❌ MALO - Sin función de reversión
operations = [
    migrations.RunPython(migrar_datos),  # No se puede revertir
]

# ✅ BUENO - Con función de reversión
operations = [
    migrations.RunPython(
        migrar_datos,
        migrations.RunPython.noop  # O función específica de reversión
    ),
]
```

#### Error 4: Pérdida de Datos

```python
# ❌ MALO - Eliminar campo sin migrar datos
operations = [
    migrations.RemoveField(
        model_name='mimodelo',
        name='campo_importante',  # Datos se pierden
    ),
]

# ✅ BUENO - Migrar datos primero, luego eliminar
operations = [
    migrations.RunPython(migrar_datos_a_nuevo_campo),
    migrations.RemoveField(
        model_name='mimodelo',
        name='campo_antiguo',
    ),
]
```

### Comandos de Verificación

#### Verificar Estado de Migraciones

```bash
# Ver estado de todas las migraciones
python manage.py showmigrations

# Ver estado de un módulo específico
python manage.py showmigrations app_name

# Ver plan de migración (qué se aplicará)
python manage.py migrate --plan
```

#### Verificar Errores

```bash
# Verificar configuración y modelos
python manage.py check

# Verificar solo migraciones
python manage.py check --deploy

# Verificar que las migraciones se pueden aplicar
python manage.py migrate --check
```

#### Probar Migraciones

```bash
# Aplicar migraciones
python manage.py migrate

# Revertir última migración
python manage.py migrate app_name previous_version

# Aplicar hasta migración específica
python manage.py migrate app_name 0005_migration_name

# Ver SQL que se ejecutará (sin aplicar)
python manage.py migrate --plan --verbosity=2
```

### Ejemplo Real: Migración de Activos

```python
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
```

**Características de esta migración:**
- ✅ Dependencias correctas
- ✅ Operaciones claras y documentadas
- ✅ Nombres descriptivos de índices
- ✅ Sin errores de sintaxis
- ✅ Reversible automáticamente

---

## Vistas (Views)

### Estructura Básica de un ViewSet

```python
"""
Views para [Nombre del Módulo]
"""
import logging
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework.pagination import PageNumberPagination

from core.mixins import EmpresaFilterMixin
from .services import MiServicio  # Si tienes servicios
from .permissions import CanAccionModelo  # Permisos personalizados
from .models import MiModelo
from .serializers import MiModeloSerializer, MiModeloListSerializer

logger = logging.getLogger(__name__)


class MiModeloPagination(PageNumberPagination):
    """Paginación personalizada para MiModelo"""
    page_size = 20
    page_size_query_param = 'page_size'
    max_page_size = 100


class MiModeloViewSet(EmpresaFilterMixin, viewsets.ModelViewSet):
    """
    ViewSet para gestionar [nombre del modelo].
    
    Endpoints:
    - GET /api/v1/modulo/modelos/ - Lista modelos
    - POST /api/v1/modulo/modelos/ - Crea nuevo modelo
    - GET /api/v1/modulo/modelos/{id}/ - Detalle de modelo
    - PUT/PATCH /api/v1/modulo/modelos/{id}/ - Actualiza modelo
    - DELETE /api/v1/modulo/modelos/{id}/ - Elimina modelo
    """
    queryset = MiModelo.objects.select_related(
        'empresa',
        'relacion_importante',
        'usuario_creacion',
        'usuario_modificacion'
    ).all()
    serializer_class = MiModeloSerializer
    permission_classes = [IsAuthenticated]
    pagination_class = MiModeloPagination
    filterset_fields = ['campo1', 'campo2', 'estado']
    search_fields = ['nombre', 'codigo', 'descripcion']
    ordering_fields = ['nombre', 'fecha_creacion', 'codigo']
    ordering = ['-fecha_creacion']
    
    def get_serializer_class(self):
        """Usar serializer diferente para listado si es necesario"""
        if self.action == 'list':
            return MiModeloListSerializer
        return MiModeloSerializer
    
    def perform_create(self, serializer):
        """Asignar empresa y usuario al crear"""
        serializer.save(
            empresa=self.request.user.empresa,
            usuario_creacion=self.request.user
        )
    
    def perform_update(self, serializer):
        """Asignar usuario de modificación al actualizar"""
        serializer.save(usuario_modificacion=self.request.user)
    
    @action(detail=True, methods=['post'], permission_classes=[IsAuthenticated, CanAccionModelo])
    def accion_personalizada(self, request, pk=None):
        """
        Acción personalizada que requiere permiso específico.
        
        ⚠️ IDEMPOTENTE: Puede ejecutarse múltiples veces sin efectos secundarios diferentes.
        
        Requiere permiso: modulo.accion_modelo (o ser staff/superuser)
        
        Request body:
            - campo: Valor del campo
        
        Returns:
            Datos del modelo actualizado.
        """
        modelo = self.get_object()
        
        # Verificar estado actual (idempotencia: no hacer nada si ya está en el estado deseado)
        campo_deseado = request.data.get('campo')
        if modelo.campo == campo_deseado:
            # Ya está en el estado deseado, retornar sin modificar (idempotente)
            return Response(MiModeloSerializer(modelo).data)
        
        # Usar servicio si existe lógica de negocio compleja
        resultado, error = MiServicio.procesar_accion(
            modelo=modelo,
            datos=request.data,
            usuario=request.user
        )
        
        if error:
            return Response(
                {'error': error},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        modelo.refresh_from_db()
        return Response(MiModeloSerializer(modelo).data)
```

### Mejores Prácticas para Vistas

#### Principios Aplicados:
- **SRP**: Vistas solo manejan requests/responses, lógica de negocio en servicios
- **SoC**: Separar presentación (vistas) de lógica de negocio (servicios)
- **DRY**: Usar mixins (`EmpresaFilterMixin`) en lugar de repetir código de filtrado
- **KISS**: Endpoints simples y directos
- **YAGNI**: No crear endpoints "por si acaso"
- **IDEMPOTENCIA**: Todas las operaciones deben ser idempotentes (OBLIGATORIO)

#### ✅ HACER:

1. **Usar `EmpresaFilterMixin`** para filtrado automático por empresa (DRY: no repetir código)
2. **Usar `select_related()`** en querysets para evitar N+1 queries
3. **Implementar paginación personalizada** para listados grandes
4. **Usar `filterset_fields`** para filtrado simple
5. **Usar `search_fields`** para búsqueda
6. **Usar `ordering_fields`** para ordenamiento
7. **Implementar `perform_create()` y `perform_update()`** para asignar empresa y usuarios
8. **Usar servicios** para lógica de negocio compleja (SRP/SoC: separar responsabilidades)
9. **Aplicar permisos personalizados** en acciones críticas con `@action(permission_classes=[...])`
10. **Documentar endpoints** con docstrings claros
11. **Usar logging** para operaciones importantes
12. **Garantizar idempotencia** en todas las acciones personalizadas (`@action`) (IDEMPOTENCIA: obligatorio)
    - Verificar estado antes de modificar
    - No crear registros duplicados
    - Retornar el mismo resultado si se ejecuta múltiples veces

#### ❌ NO HACER:

1. ❌ No poner lógica de negocio compleja directamente en las vistas (SRP/SoC: usar servicios)
2. ❌ No olvidar `select_related()` en querysets con relaciones
3. ❌ No permitir acceso sin autenticación (siempre `IsAuthenticated`)
4. ❌ No olvidar filtrar por empresa (DRY: usar mixin)
5. ❌ No crear acciones sin documentar
6. ❌ No duplicar código de filtrado por empresa (DRY: usar `EmpresaFilterMixin`)
7. ❌ No crear endpoints innecesarios (YAGNI: solo lo que se necesita)
8. ❌ **NO crear operaciones no idempotentes** - Todas las acciones deben poder ejecutarse múltiples veces sin efectos secundarios diferentes (IDEMPOTENCIA: obligatorio)

### Ejemplo Real: ActivoFijoViewSet

```python
class ActivoFijoViewSet(EmpresaFilterMixin, viewsets.ModelViewSet):
    queryset = ActivoFijo.objects.select_related(
        'tipo_activo',
        'responsable',
        'empresa',
        'usuario_creacion',
        'usuario_modificacion'
    ).all()
    permission_classes = [IsAuthenticated]
    pagination_class = ActivosPagination
    
    @action(detail=True, methods=['post'], permission_classes=[IsAuthenticated, CanDepreciarActivo])
    def depreciar(self, request, pk=None):
        """Registra depreciación usando servicio"""
        activo = self.get_object()
        
        # Usar servicio para lógica de negocio
        depreciacion, error = DepreciacionService.registrar_depreciacion(
            activo=activo,
            fecha=request.data.get('fecha'),
            usuario=request.user,
            observacion=request.data.get('observacion', '')
        )
        
        if error:
            return Response({'error': error}, status=status.HTTP_400_BAD_REQUEST)
        
        activo.refresh_from_db()
        return Response(DepreciacionSerializer(depreciacion).data)
```

---

## Serializers

### Estructura Básica de un Serializer

```python
"""
Serializers para [Nombre del Módulo]
"""
from rest_framework import serializers
from .models import MiModelo


class MiModeloSerializer(serializers.ModelSerializer):
    """Serializer completo para MiModelo"""
    
    # Campos relacionados (read-only)
    relacion_nombre = serializers.CharField(source='relacion.nombre', read_only=True)
    
    # Campos calculados (read-only)
    campo_calculado = serializers.DecimalField(
        max_digits=14, decimal_places=2, read_only=True
    )
    
    class Meta:
        model = MiModelo
        fields = [
            'id', 'empresa', 'nombre', 'codigo',
            'relacion', 'relacion_nombre',
            'campo_calculado',
            'uuid', 'fecha_creacion', 'fecha_actualizacion',
            'usuario_creacion', 'usuario_modificacion'
        ]
        read_only_fields = [
            'uuid', 'fecha_creacion', 'fecha_actualizacion',
            'usuario_creacion', 'usuario_modificacion', 'empresa'
        ]
    
    def validate_relacion(self, value):
        """
        Valida que la relación pertenezca a la misma empresa del usuario.
        
        CRÍTICO: Siempre validar empresa en relaciones.
        """
        request = self.context.get('request')
        if request and hasattr(request.user, 'empresa'):
            user_empresa = request.user.empresa
            if value.empresa is not None and user_empresa is not None:
                if value.empresa != user_empresa:
                    raise serializers.ValidationError(
                        'La relación debe pertenecer a su empresa'
                    )
        return value
    
    def validate(self, data):
        """
        Validaciones adicionales que requieren múltiples campos.
        """
        campo1 = data.get('campo1')
        campo2 = data.get('campo2')
        
        # Validar reglas de negocio
        if campo1 is not None and campo2 is not None:
            if campo1 > campo2:
                raise serializers.ValidationError({
                    'campo1': 'Campo1 no puede ser mayor que Campo2'
                })
        
        return data


class MiModeloListSerializer(serializers.ModelSerializer):
    """Serializer optimizado para listado (menos campos)"""
    
    class Meta:
        model = MiModelo
        fields = ['id', 'codigo', 'nombre', 'estado', 'fecha_creacion']
```

### Mejores Prácticas para Serializers

#### Principios Aplicados:
- **SRP**: Serializers solo manejan serialización y validación de entrada
- **DRY**: Validación de empresa centralizada en `validate_[campo]()`, no repetir
- **SoC**: Separar validación de entrada (serializers) de validación de datos (modelos)
- **KISS**: Validaciones simples y directas

#### ✅ HACER:

1. **Siempre validar empresa** en relaciones (`validate_[campo]()`) (DRY: método reutilizable)
2. **Usar `read_only_fields`** para campos de auditoría y empresa
3. **Crear serializer separado para listado** si tiene muchos campos (SRP: responsabilidad específica)
4. **Validar reglas de negocio** en `validate()` cuando requieren múltiples campos
5. **Usar `source`** para campos relacionados en lugar de métodos (KISS: más simple)
6. **Documentar validaciones** con docstrings

#### ❌ NO HACER:

1. ❌ No permitir que usuarios asignen objetos de otra empresa
2. ❌ No hacer campos editables que deberían ser read-only
3. ❌ No olvidar validar empresa en relaciones (DRY: siempre usar el mismo patrón)
4. ❌ No duplicar validaciones de empresa (DRY: método reutilizable)
5. ❌ No poner lógica de negocio en serializers (SRP: solo validación de entrada)

### Ejemplo Real: ActivoFijoSerializer

```python
class ActivoFijoSerializer(serializers.ModelSerializer):
    tipo_activo_nombre = serializers.CharField(source='tipo_activo.nombre', read_only=True)
    responsable_nombre = serializers.CharField(source='responsable.username', read_only=True)
    
    def validate_tipo_activo(self, value):
        """Valida que el tipo_activo pertenezca a la misma empresa del usuario"""
        request = self.context.get('request')
        if request and hasattr(request.user, 'empresa'):
            user_empresa = request.user.empresa
            if value.empresa is not None and user_empresa is not None:
                if value.empresa != user_empresa:
                    raise serializers.ValidationError(
                        'El tipo de activo debe pertenecer a su empresa'
                    )
        return value
```

---

## Permisos (Permissions)

### ⚠️ IMPORTANTE: Usar el Nuevo Modelo de Seguridad Global

**SIEMPRE usar las clases base genéricas de `core.permissions`**

### Estructura Básica de Permisos

```python
"""
Permisos personalizados para el módulo [Nombre del Módulo]

Usa las clases base genéricas de core.permissions para
eliminar código duplicado y mantener consistencia.
"""
from core.permissions import BaseEmpresaPermission
from core.permissions.mixins import ResponsableValidationMixin, AdminStaffMixin
from rest_framework import permissions


class CanAccionModelo(BaseEmpresaPermission):
    """
    Permiso para realizar acción específica en modelo.
    
    Permite la operación si el usuario:
    - Es superusuario o staff, O
    - Tiene el permiso 'modulo.accion_modelo'
    """
    
    def __init__(self):
        super().__init__(
            permission_codename='modulo.accion_modelo',
            message='No tiene permiso para realizar esta acción.'
        )


class IsModeloResponsable(ResponsableValidationMixin, AdminStaffMixin, permissions.BasePermission):
    """
    Permiso que verifica si el usuario es el responsable del modelo.
    
    Útil para permitir que responsables realicen
    ciertas operaciones sobre los modelos a su cargo.
    """
    message = 'Solo el responsable puede realizar esta operación.'
    
    def has_object_permission(self, request, view, obj):
        if not request.user.is_authenticated:
            return False
        
        # Superusuarios y staff siempre tienen acceso
        if self._is_admin_or_staff(request.user):
            return True
        
        # Verificar si el usuario es el responsable
        return self._is_responsable(obj, request.user)
```

### Mejores Prácticas para Permisos

#### Principios Aplicados:
- **DRY**: SIEMPRE usar clases base genéricas, nunca duplicar código
- **SRP**: Permisos solo verifican acceso, no lógica de negocio
- **SoC**: Separar verificación de permisos de lógica de negocio
- **KISS**: Configuración simple usando clases base

#### ✅ HACER:

1. **SIEMPRE usar `BaseEmpresaPermission`** para permisos con validación de empresa (DRY: no duplicar código)
2. **Usar mixins genéricos** (`ResponsableValidationMixin`, `AdminStaffMixin`) cuando sea apropiado (DRY: reutilizar)
3. **Definir permisos en `Meta.permissions`** del modelo
4. **Aplicar permisos en acciones críticas** con `@action(permission_classes=[...])`
5. **Documentar qué permiso requiere** cada acción

#### ❌ NO HACER:

1. ❌ **NO crear permisos desde cero** - siempre usar clases base (DRY: violación crítica)
2. ❌ No duplicar código de verificación de autenticación/admin/staff/empresa (DRY: usar clases base)
3. ❌ No olvidar aplicar permisos en acciones críticas
4. ❌ No crear clases de permisos con lógica de negocio (SRP: solo verificación de acceso)
5. ❌ No repetir el mismo código de verificación en múltiples permisos (DRY: usar `BaseEmpresaPermission`)

### Ejemplo Real: Activos Permissions

```python
from core.permissions import BaseEmpresaPermission

class CanDepreciarActivo(BaseEmpresaPermission):
    def __init__(self):
        super().__init__(
            permission_codename='activos.depreciar_activofijo',
            message='No tiene permiso para registrar depreciaciones de activos.'
        )
```

---

## Servicios (Services)

### ⚠️ RECOMENDADO: Separar Lógica de Negocio

**Crear `services.py` para lógica de negocio compleja**

### Estructura Básica de Servicios

```python
"""
Servicios de negocio para el módulo [Nombre del Módulo]

Este módulo contiene la lógica de negocio separada de las vistas,
facilitando la testabilidad y mantenibilidad.
"""
import logging
from decimal import Decimal
from typing import Optional, Tuple
from django.db import transaction
from django.core.exceptions import ValidationError

from .models import MiModelo
from .constants import ESTADOS_VALIDOS, TOLERANCIA_DECIMAL

logger = logging.getLogger(__name__)


class MiServicio:
    """
    Servicio para gestionar operaciones de negocio relacionadas con MiModelo.
    """
    
    @staticmethod
    def puede_realizar_accion(modelo: MiModelo) -> Tuple[bool, Optional[str]]:
        """
        Verifica si se puede realizar una acción.
        
        Args:
            modelo: Instancia de MiModelo
        
        Returns:
            Tuple (puede_realizar, mensaje_error)
        """
        if modelo.estado not in ESTADOS_VALIDOS:
            return False, f'El modelo debe estar en estado válido'
        
        return True, None
    
    @classmethod
    def procesar_accion(
        cls,
        modelo: MiModelo,
        datos: dict,
        usuario
    ) -> Tuple[Optional[MiModelo], Optional[str]]:
        """
        Procesa una acción de negocio.
        
        ⚠️ IDEMPOTENTE: Puede ejecutarse múltiples veces sin efectos secundarios diferentes.
        
        Args:
            modelo: Instancia de MiModelo
            datos: Datos para procesar
            usuario: Usuario que realiza la acción
        
        Returns:
            Tuple (modelo_actualizado, mensaje_error)
        """
        # Validar que se puede realizar
        puede, error = cls.puede_realizar_accion(modelo)
        if not puede:
            return None, error
        
        # Verificar estado actual (idempotencia: no hacer nada si ya está en el estado deseado)
        campo_deseado = datos.get('campo')
        if modelo.campo == campo_deseado:
            # Ya está en el estado deseado, retornar sin modificar (idempotente)
            logger.info(f"Acción ya aplicada para {modelo}, retornando sin cambios")
            return modelo, None
        
        # Procesar con transacción
        try:
            with transaction.atomic():
                # Refrescar desde BD para evitar condiciones de carrera
                modelo.refresh_from_db()
                
                # Verificar nuevamente después de refrescar (idempotencia)
                if modelo.campo == campo_deseado:
                    return modelo, None
                
                # Lógica de negocio
                modelo.campo = campo_deseado
                modelo.save()
                
                logger.info(f"Acción procesada para {modelo} por {usuario}")
                
                return modelo, None
        except Exception as e:
            logger.error(f"Error procesando acción: {e}")
            return None, str(e)
```

### Mejores Prácticas para Servicios

#### Principios Aplicados:
- **SRP**: Servicios tienen una sola responsabilidad (lógica de negocio específica)
- **SoC**: Separar lógica de negocio (servicios) de presentación (vistas) y datos (modelos)
- **DRY**: Centralizar lógica de negocio reutilizable en servicios
- **KISS**: Métodos simples y directos
- **YAGNI**: Solo crear servicios cuando realmente se necesita lógica de negocio compleja
- **IDEMPOTENCIA**: Todos los métodos de servicio deben ser idempotentes (OBLIGATORIO)

#### ✅ HACER:

1. **Usar clases con métodos estáticos** o `@classmethod` (KISS: simple y directo)
2. **Usar transacciones** (`transaction.atomic()`) para operaciones que modifican múltiples objetos
3. **Retornar tuplas** `(resultado, error)` para manejo consistente de errores (DRY: patrón consistente)
4. **Usar logging** para operaciones importantes
5. **Validar antes de procesar**
6. **Usar constantes** del módulo en lugar de valores hardcodeados (DRY: no repetir valores)
7. **Garantizar idempotencia** en todos los métodos (IDEMPOTENCIA: obligatorio)
    - Verificar estado actual antes de modificar
    - No crear registros duplicados (verificar existencia)
    - Retornar el mismo resultado si se ejecuta múltiples veces
    - Usar identificadores únicos para verificar si la operación ya se realizó

#### ❌ NO HACER:

1. ❌ No poner lógica de negocio en modelos o vistas (SRP/SoC: separar responsabilidades)
2. ❌ No olvidar manejo de errores
3. ❌ No hacer operaciones sin transacciones cuando modifican múltiples objetos
4. ❌ No crear servicios para lógica trivial (YAGNI: solo cuando es necesario)
5. ❌ No duplicar lógica de negocio en múltiples servicios (DRY: centralizar)
6. ❌ **NO crear métodos no idempotentes** - Todos los métodos deben poder ejecutarse múltiples veces sin efectos secundarios diferentes (IDEMPOTENCIA: obligatorio)

---

## Señales (Signals)

### Estructura Básica de Señales

```python
"""
Señales de Django para el módulo [Nombre del Módulo]

Estas señales automatizan comportamientos del sistema:
- Actualización automática de estados
- Notificaciones de eventos importantes
- Logging de cambios críticos
"""
import logging
from django.db.models.signals import post_save, pre_save
from django.dispatch import receiver

from .models import MiModelo
from .constants import ESTADO_FINAL

logger = logging.getLogger(__name__)


@receiver(pre_save, sender=MiModelo)
def modelo_pre_save(sender, instance, **kwargs):
    """
    Señal pre-save para MiModelo.
    - Actualiza automáticamente el estado si se cumplen condiciones
    """
    # Solo actuar si es un update (tiene pk)
    if instance.pk:
        # Lógica de actualización automática
        if instance.campo <= 0:
            instance.estado = ESTADO_FINAL
            logger.info(f"Modelo {instance.codigo} actualizado automáticamente")


@receiver(post_save, sender=MiModelo)
def modelo_post_save(sender, instance, created, **kwargs):
    """
    Señal post-save para MiModelo.
    - Log de creación de nuevos modelos
    - Alertas de condiciones especiales
    """
    if created:
        logger.info(f"Nuevo modelo creado: {instance.codigo} - {instance.nombre}")
```

### Registrar Señales en `apps.py`

```python
from django.apps import AppConfig


class MiModuloConfig(AppConfig):
    name = 'mi_modulo'
    verbose_name = 'Mi Módulo'
    
    def ready(self):
        """Registra las señales cuando la aplicación está lista"""
        import mi_modulo.signals  # noqa: F401
```

---

## Constantes (Constants)

### Estructura Básica de Constantes

```python
"""
Constantes para el módulo [Nombre del Módulo]
"""
from decimal import Decimal

# Estados del modelo
ESTADO_ACTIVO = 'ACTIVO'
ESTADO_INACTIVO = 'INACTIVO'
ESTADO_FINAL = 'FINAL'

ESTADO_CHOICES = (
    (ESTADO_ACTIVO, 'Activo'),
    (ESTADO_INACTIVO, 'Inactivo'),
    (ESTADO_FINAL, 'Final'),
)

ESTADOS_VALIDOS = [e[0] for e in ESTADO_CHOICES]

# Valores por defecto
VALOR_DEFAULT = Decimal('0.00')
PORCENTAJE_DEFAULT = Decimal('0.00')

# Tolerancias
TOLERANCIA_DECIMAL = Decimal('0.01')

# Límites
VALOR_MAX = Decimal('999999.99')
VALOR_MIN = Decimal('0.00')
```

### Mejores Prácticas para Constantes

#### Principios Aplicados:
- **DRY**: Centralizar valores para no repetirlos en múltiples lugares
- **KISS**: Valores simples y directos
- **SoC**: Separar constantes de código lógico

#### ✅ HACER:

1. **Centralizar todas las constantes** en un archivo (DRY: no repetir valores)
2. **Usar nombres descriptivos** en mayúsculas
3. **Agrupar constantes relacionadas**
4. **Documentar el propósito** de constantes complejas

#### ❌ NO HACER:

1. ❌ No hardcodear valores en múltiples lugares (DRY: usar constantes)
2. ❌ No crear constantes "por si acaso" (YAGNI: solo lo necesario)

---

## Admin

### Estructura Básica de Admin

```python
from django.contrib import admin
from .models import MiModelo


@admin.register(MiModelo)
class MiModeloAdmin(admin.ModelAdmin):
    """Admin para MiModelo"""
    
    list_display = [
        'codigo', 'nombre', 'empresa', 'estado', 'fecha_creacion'
    ]
    list_filter = ['estado', 'empresa', 'fecha_creacion']
    search_fields = ['codigo', 'nombre', 'descripcion']
    ordering = ['-fecha_creacion']
    readonly_fields = [
        'uuid', 'fecha_creacion', 'fecha_actualizacion',
        'campo_calculado'
    ]
    autocomplete_fields = ['relacion']  # Si tiene relaciones
    date_hierarchy = 'fecha_creacion'
    
    fieldsets = (
        ('Información General', {
            'fields': ('empresa', 'codigo', 'nombre', 'descripcion', 'estado')
        }),
        ('Relaciones', {
            'fields': ('relacion',)
        }),
        ('Metadata', {
            'fields': ('uuid', 'fecha_creacion', 'fecha_actualizacion'),
            'classes': ('collapse',)
        }),
    )
```

### Mejores Prácticas para Admin

#### ✅ HACER:

1. **Configurar `list_display`** con campos importantes
2. **Usar `list_filter`** para filtros útiles
3. **Usar `search_fields`** para búsqueda
4. **Usar `autocomplete_fields`** para relaciones grandes
5. **Usar `fieldsets`** para organizar campos
6. **Marcar campos calculados como `readonly_fields`**

---

## Tests

### Estructura Básica de Tests

```python
"""
Tests para [Nombre del Módulo]
"""
from django.test import TestCase
from django.contrib.auth import get_user_model
from rest_framework.test import APITestCase, APIClient
from rest_framework import status
from decimal import Decimal

from .models import MiModelo
from empresas.models import Empresa

User = get_user_model()


# ========== TESTS DE MODELOS ==========

class MiModeloModelTest(TestCase):
    """Tests para el modelo MiModelo"""
    
    def setUp(self):
        """Configuración inicial para cada test"""
        self.empresa = Empresa.objects.create(
            nombre='Empresa Test',
            rnc='123456789'
        )
        self.user = User.objects.create_user(
            username='testuser',
            password='testpass',
            empresa=self.empresa
        )
    
    def test_crear_modelo(self):
        """Test: Crear modelo"""
        modelo = MiModelo.objects.create(
            empresa=self.empresa,
            codigo='TEST001',
            nombre='Modelo Test'
        )
        self.assertIsNotNone(modelo.id)
        self.assertEqual(modelo.codigo, 'TEST001')
    
    def test_modelo_str(self):
        """Test: Representación string del modelo"""
        modelo = MiModelo.objects.create(
            empresa=self.empresa,
            codigo='TEST001',
            nombre='Modelo Test'
        )
        self.assertIn('TEST001', str(modelo))


# ========== TESTS DE VALIDACIONES ==========

class MiModeloValidacionesTest(TestCase):
    """Tests para validaciones de negocio"""
    
    def setUp(self):
        self.empresa = Empresa.objects.create(
            nombre='Empresa Test',
            rnc='123456789'
        )
    
    def test_valor_negativo_error(self):
        """Test: Valor negativo genera error"""
        modelo = MiModelo(
            empresa=self.empresa,
            codigo='TEST001',
            nombre='Test',
            valor=Decimal('-10.00')
        )
        with self.assertRaises(ValidationError):
            modelo.full_clean()


# ========== TESTS DE API ==========

class MiModeloAPITest(APITestCase):
    """Tests para API de MiModelo"""
    
    def setUp(self):
        self.client = APIClient()
        self.empresa = Empresa.objects.create(
            nombre='Empresa Test',
            rnc='123456789'
        )
        self.user = User.objects.create_user(
            username='testuser',
            password='testpass',
            empresa=self.empresa
        )
    
    def test_listar_modelos(self):
        """Test: Listar modelos requiere autenticación"""
        self.client.force_authenticate(user=self.user)
        response = self.client.get('/api/v1/modulo/modelos/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
    
    def test_sin_autenticacion_recibe_401(self):
        """Test: Sin autenticación retorna 401"""
        response = self.client.get('/api/v1/modulo/modelos/')
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
```

### Mejores Prácticas para Tests

#### Principios Aplicados:
- **DRY**: Usar `setUp()` para configuración común, no repetir código
- **SRP**: Cada test prueba una cosa específica
- **KISS**: Tests simples y directos
- **YAGNI**: Probar solo lo necesario, no casos hipotéticos

#### ✅ HACER:

1. **Organizar tests por categorías** (Modelos, Validaciones, API, Servicios, Permisos) (SRP: separar por responsabilidad)
2. **Usar `setUp()`** para configuración común (DRY: no repetir código)
3. **Nombrar tests descriptivamente** (`test_[que_se_prueba]`)
4. **Probar casos positivos y negativos**
5. **Probar validaciones de negocio**
6. **Probar permisos** si hay acciones con permisos personalizados
7. **Usar `APITestCase`** para tests de API
8. **Usar `force_authenticate()`** para tests de API autenticados

#### ❌ NO HACER:

1. ❌ No crear tests sin propósito claro (YAGNI: solo lo necesario)
2. ❌ No duplicar código de setup (DRY: usar `setUp()`)
3. ❌ No probar solo casos felices
4. ❌ No crear tests para funcionalidad hipotética (YAGNI)
5. ❌ No repetir código de configuración en cada test (DRY: usar `setUp()`)

---

## Apps Config

### Estructura Básica de Apps Config

```python
from django.apps import AppConfig


class MiModuloConfig(AppConfig):
    name = 'mi_modulo'
    verbose_name = 'Mi Módulo'
    
    def ready(self):
        """Registra las señales cuando la aplicación está lista"""
        import mi_modulo.signals  # noqa: F401
```

---

## Checklist de Implementación

### Para Nuevos Módulos

#### Estructura Básica
- [ ] Crear estructura de directorios estándar
- [ ] Crear `__init__.py`
- [ ] Crear `apps.py` con configuración
- [ ] Crear `models.py` con modelos
- [ ] Crear `admin.py` con configuración de admin
- [ ] Crear `serializers.py` con serializers
- [ ] Crear `views.py` con ViewSets
- [ ] Crear `urls.py` con rutas
- [ ] Crear `tests.py` con tests básicos

#### Migraciones (CRÍTICO: Verificar Siempre)
- [ ] Crear migración inicial (`python manage.py makemigrations`)
- [ ] **Verificar que la migración no tiene errores de sintaxis** (`python manage.py makemigrations --dry-run`)
- [ ] **Verificar plan de migración** (`python manage.py migrate --plan`)
- [ ] **Verificar que se puede aplicar** (`python manage.py migrate`)
- [ ] **Verificar que se puede revertir** (`python manage.py migrate app_name previous_version`)
- [ ] **Probar migración en desarrollo antes de commitear**
- [ ] **Verificar dependencias** están correctas (todas existen)
- [ ] **Documentar migraciones complejas** con comentarios
- [ ] **Ejecutar `python manage.py check`** después de crear migraciones
- [ ] **Ejecutar `python manage.py check --deploy`** para verificar migraciones
- [ ] **Ejecutar tests** después de aplicar migraciones (`python manage.py test app_name`)
- [ ] **Verificar estado de migraciones** (`python manage.py showmigrations app_name`)
- [ ] **NO commitear migraciones con errores** (corregir antes de commitear)
- [ ] **Garantizar idempotencia en migraciones personalizadas** (IDEMPOTENCIA: obligatorio)
  - [ ] En `RunPython`, verificar estado antes de modificar datos
  - [ ] No crear registros duplicados en migraciones de datos
  - [ ] Probar que la migración puede ejecutarse múltiples veces sin errores

#### Modelos (CRÍTICO: Integridad de Datos)
- [ ] Campo `empresa` con `db_index=True`
- [ ] Campos de auditoría (uuid, fechas, usuarios)
- [ ] **Método `clean()` COMPLETO con TODAS las validaciones** (OBLIGATORIO)
  - [ ] Validar valores numéricos (no negativos, rangos)
  - [ ] Validar fechas (no futuras, consistencia)
  - [ ] Validar relaciones (empresa, integridad referencial)
  - [ ] Validar consistencia entre campos relacionados
  - [ ] Validar reglas de negocio específicas
  - [ ] Validar transiciones de estado (si aplica)
- [ ] **`save()` con `full_clean()`** para garantizar validaciones siempre
- [ ] Método `__str__()` descriptivo
- [ ] `Meta` con `verbose_name`, `ordering`, `indexes`
- [ ] `Meta` con `unique_together` si aplica (garantizar unicidad)
- [ ] `related_name` descriptivo en ForeignKeys
- [ ] `on_delete` apropiado (PROTECT para críticos - protege integridad)
- [ ] **NO dejar campos sin validar** - Todos los campos críticos deben tener validación
- [ ] **Probar validaciones con tests** - Asegurar que funcionan correctamente

#### Vistas
- [ ] Usar `EmpresaFilterMixin`
- [ ] Usar `select_related()` en queryset
- [ ] Implementar paginación personalizada
- [ ] `filterset_fields`, `search_fields`, `ordering_fields`
- [ ] `perform_create()` y `perform_update()`
- [ ] Documentar endpoints con docstrings
- [ ] **Garantizar idempotencia en acciones personalizadas (`@action`)** (IDEMPOTENCIA: obligatorio)
  - [ ] Verificar estado antes de modificar
  - [ ] No crear registros duplicados
  - [ ] Retornar el mismo resultado si se ejecuta múltiples veces

#### Serializers
- [ ] Validar empresa en relaciones (`validate_[campo]()`)
- [ ] `read_only_fields` para auditoría
- [ ] Serializer separado para listado si es necesario
- [ ] Validaciones de negocio en `validate()`

#### Permisos
- [ ] **Usar `BaseEmpresaPermission`** (NO crear desde cero)
- [ ] Definir permisos en `Meta.permissions` del modelo
- [ ] Aplicar permisos en acciones críticas
- [ ] Usar mixins genéricos cuando sea apropiado

#### Servicios (Opcional pero Recomendado)
- [ ] Crear `services.py` si hay lógica de negocio compleja
- [ ] Usar transacciones para operaciones múltiples
- [ ] Retornar tuplas `(resultado, error)`
- [ ] Usar logging
- [ ] **Garantizar idempotencia en todos los métodos** (IDEMPOTENCIA: obligatorio)
  - [ ] Verificar estado actual antes de modificar
  - [ ] No crear registros duplicados (verificar existencia)
  - [ ] Retornar el mismo resultado si se ejecuta múltiples veces

#### Constantes (Opcional pero Recomendado)
- [ ] Crear `constants.py` con constantes centralizadas
- [ ] Estados, valores por defecto, tolerancias

#### Señales (Opcional)
- [ ] Crear `signals.py` si hay automatizaciones
- [ ] Registrar en `apps.py`

#### Tests
- [ ] Tests de modelos
- [ ] Tests de validaciones
- [ ] Tests de API
- [ ] Tests de permisos (si hay permisos personalizados)
- [ ] Tests de servicios (si hay servicios)
- [ ] **Tests de idempotencia** (IDEMPOTENCIA: obligatorio)
  - [ ] Probar que acciones pueden ejecutarse múltiples veces sin efectos secundarios diferentes
  - [ ] Probar que servicios retornan el mismo resultado en ejecuciones repetidas

#### Admin
- [ ] `list_display` con campos importantes
- [ ] `list_filter` útil
- [ ] `search_fields` configurado
- [ ] `fieldsets` organizados

#### Principios de Diseño (Verificar en Todo el Módulo)
- [ ] **DRY**: No hay código duplicado (usar clases base, mixins, servicios)
- [ ] **KISS**: Código simple y directo, sin sobre-ingeniería
- [ ] **SRP**: Cada clase/módulo tiene una sola responsabilidad
- [ ] **SoC**: Capas separadas (modelos, vistas, servicios, serializers)
- [ ] **YAGNI**: Solo funcionalidad necesaria, nada "por si acaso"
- [ ] **IDEMPOTENCIA**: Todas las operaciones son idempotentes (OBLIGATORIO)
  - [ ] Endpoints pueden ejecutarse múltiples veces sin efectos secundarios diferentes
  - [ ] Servicios retornan el mismo resultado en ejecuciones repetidas
  - [ ] Migraciones pueden ejecutarse múltiples veces sin errores

---

## Ejemplo Completo: Módulo de Referencia

**El módulo `activos` es el ejemplo de referencia** para seguir estas prácticas.

### Archivos de Referencia

- `backend/activos/models.py` - Modelos con validaciones y GeneratedField
- `backend/activos/views.py` - ViewSets con servicios y permisos
- `backend/activos/serializers.py` - Serializers con validación de empresa
- `backend/activos/permissions.py` - Permisos usando clases base genéricas
- `backend/activos/services.py` - Servicios con lógica de negocio
- `backend/activos/signals.py` - Señales automatizadas
- `backend/activos/constants.py` - Constantes centralizadas
- `backend/activos/admin.py` - Admin completamente configurado
- `backend/activos/tests.py` - Tests completos

---

## Recursos Adicionales

### Documentación Relacionada

- [Manejo de Permisos Globales](./Manejo%20de%20permisos%20globales.md) - Sistema de permisos genérico
- [Análisis QA Activos Fijos](./Activos%20Fijos.md) - Problemas resueltos y mejoras

### Referencias Django 6.0

- [GeneratedField](https://docs.djangoproject.com/en/6.0/ref/models/fields/#generatedfield)
- [Database Indexes](https://docs.djangoproject.com/en/6.0/ref/models/indexes/)
- [Model Validation](https://docs.djangoproject.com/en/6.0/ref/models/instances/#validating-objects)

---

**Última Actualización:** 2025-01-27  
**Versión:** 1.0  
**Mantenido por:** Equipo de Desarrollo

