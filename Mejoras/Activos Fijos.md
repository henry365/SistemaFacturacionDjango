# Análisis QA - Módulo Activos Fijos

**Fecha:** 2025-01-27  
**Módulo:** `backend/activos`  
**Analista:** QA Team  
**Estado:** Pendiente de Resolución

---

## Resumen Ejecutivo

El módulo de Activos Fijos gestiona la administración de activos fijos de la empresa, tipos de activos y depreciaciones. El módulo es funcional pero presenta **problemas críticos** que deben ser resueltos antes de considerar el módulo como estable para producción.

**Calificación General:** 5.5/10

---

## Problemas Críticos (Alta Prioridad - Bloqueantes)

### 🔴 CRÍTICO-001: Error de Sintaxis en `models.py` línea 85
**Archivo:** `backend/activos/models.py`  
**Línea:** 85  
**Severidad:** CRÍTICA  
**Estado:** Pendiente

**Descripción:**
La línea 85 tiene un error de sintaxis. El campo `valor_libro_actual` parece estar incompleto o mal formado.

**Código Actual:**
```python
valor_libro_actual = models.DecimalField(max_digits=14, decimal_places=2, help_text="Valor tras depreciacion acumulada")
```

**Problema Detectado:**
- Falta validación de que el campo esté correctamente definido
- Posible problema de formato

**Acción Requerida:**
- Verificar que la línea 85 esté completa y correctamente formateada
- Asegurar que el campo tenga todos los parámetros necesarios

---

### 🔴 CRÍTICO-002: Error de Indentación en `models.py` línea 123
**Archivo:** `backend/activos/models.py`  
**Línea:** 123  
**Severidad:** CRÍTICA  
**Estado:** Pendiente

**Descripción:**
El decorador `@property` para el método `porcentaje_depreciado` no está correctamente indentado dentro de la clase `ActivoFijo`.

**Código Actual:**
```python
@property
def porcentaje_depreciado(self):
    """Retorna el porcentaje de depreciacion"""
    if self.valor_adquisicion > 0:
        return round((self.depreciacion_acumulada / self.valor_adquisicion) * 100, 2)
    return 0
```

**Problema Detectado:**
- El decorador `@property` debe estar indentado al mismo nivel que otros métodos de la clase
- Actualmente parece estar fuera de la clase o mal indentado

**Acción Requerida:**
- Corregir la indentación del método `porcentaje_depreciado` para que esté correctamente dentro de la clase `ActivoFijo`
- Verificar que el método esté al mismo nivel de indentación que `__str__`

---

### 🔴 CRÍTICO-003: Bug Lógico en Actualización de Estado después de Depreciación
**Archivo:** `backend/activos/views.py`  
**Línea:** 134  
**Severidad:** CRÍTICA  
**Estado:** Pendiente

**Descripción:**
Después de crear una depreciación, se verifica `activo.valor_libro_actual` para actualizar el estado, pero el objeto no se refresca desde la base de datos después de que `Depreciacion.save()` actualiza el valor libro.

**Código Actual:**
```python
with transaction.atomic():
    depreciacion = Depreciacion.objects.create(
        activo=activo,
        fecha=fecha,
        monto=monto_depreciacion,
        valor_libro_anterior=valor_libro_anterior,
        valor_libro_nuevo=valor_libro_nuevo,
        observacion=observacion,
        usuario_creacion=request.user
    )

    # Actualizar estado si esta totalmente depreciado
    if activo.valor_libro_actual <= 0:  # ❌ activo no está actualizado
        activo.estado = 'DEPRECIADO'
        activo.save(update_fields=['estado'])
```

**Problema Detectado:**
- El objeto `activo` en memoria no refleja el nuevo `valor_libro_actual` después de que `Depreciacion.save()` lo actualiza
- La condición `if activo.valor_libro_actual <= 0` usa el valor antiguo
- Debería usar `valor_libro_nuevo` o refrescar el objeto desde la BD

**Acción Requerida:**
- Refrescar el objeto `activo` desde la base de datos después de crear la depreciación, O
- Usar `valor_libro_nuevo` directamente en la condición: `if valor_libro_nuevo <= 0`

**Código Sugerido:**
```python
with transaction.atomic():
    depreciacion = Depreciacion.objects.create(...)
    
    # Refrescar activo para obtener valor_libro_actual actualizado
    activo.refresh_from_db()
    
    # Actualizar estado si esta totalmente depreciado
    if activo.valor_libro_actual <= 0:
        activo.estado = 'DEPRECIADO'
        activo.save(update_fields=['estado'])
```

---

### 🔴 CRÍTICO-004: Error en Cálculo de Depreciación - Usa Valor Incorrecto
**Archivo:** `backend/activos/views.py`  
**Línea:** 115-117  
**Severidad:** CRÍTICA  
**Estado:** Pendiente

**Descripción:**
El cálculo de depreciación usa `valor_adquisicion` en lugar de `valor_libro_actual`, lo cual es incorrecto desde el punto de vista contable.

**Código Actual:**
```python
# Calcular depreciacion
tasa_mensual = activo.tipo_activo.porcentaje_depreciacion_anual / Decimal('12') / Decimal('100')
monto_depreciacion = activo.valor_adquisicion * tasa_mensual  # ❌ Debería ser valor_libro_actual
monto_depreciacion = min(monto_depreciacion, activo.valor_libro_actual)
```

**Problema Detectado:**
- La depreciación debe calcularse sobre el valor libro actual, no sobre el valor de adquisición
- Esto causa que la depreciación sea incorrecta para activos que ya tienen depreciación acumulada

**Acción Requerida:**
- Cambiar el cálculo para usar `valor_libro_actual` en lugar de `valor_adquisicion`
- Verificar que el cálculo sea consistente con las prácticas contables estándar

**Código Sugerido:**
```python
# Calcular depreciacion sobre valor libro actual
tasa_mensual = activo.tipo_activo.porcentaje_depreciacion_anual / Decimal('12') / Decimal('100')
monto_depreciacion = activo.valor_libro_actual * tasa_mensual
monto_depreciacion = min(monto_depreciacion, activo.valor_libro_actual)
```

---

## Problemas de Calidad (Media Prioridad)

### 🟡 CALIDAD-001: Falta Validación de Negocio en Modelo `TipoActivo`
**Archivo:** `backend/activos/models.py`  
**Clase:** `TipoActivo`  
**Severidad:** MEDIA  
**Estado:** Pendiente

**Descripción:**
El modelo `TipoActivo` no valida que `porcentaje_depreciacion_anual` esté en un rango válido (0-100).

**Problema Detectado:**
- No hay validación que impida valores negativos o mayores a 100
- No hay validación que `vida_util_anos` sea positivo

**Acción Requerida:**
- Agregar método `clean()` en el modelo para validar:
  - `porcentaje_depreciacion_anual` entre 0 y 100
  - `vida_util_anos` > 0
- Agregar validación en el serializer también

**Código Sugerido:**
```python
def clean(self):
    if self.porcentaje_depreciacion_anual < 0 or self.porcentaje_depreciacion_anual > 100:
        raise ValidationError({
            'porcentaje_depreciacion_anual': 'El porcentaje debe estar entre 0 y 100'
        })
    if self.vida_util_anos <= 0:
        raise ValidationError({
            'vida_util_anos': 'La vida útil debe ser mayor a 0'
        })
```

---

### 🟡 CALIDAD-002: Falta Validación de Negocio en Modelo `ActivoFijo`
**Archivo:** `backend/activos/models.py`  
**Clase:** `ActivoFijo`  
**Severidad:** MEDIA  
**Estado:** Pendiente

**Descripción:**
El modelo `ActivoFijo` no valida reglas de negocio importantes.

**Problemas Detectados:**
1. No valida que `valor_libro_actual` <= `valor_adquisicion`
2. No valida que `fecha_adquisicion` no sea futura
3. No valida que `valor_adquisicion` y `valor_libro_actual` sean >= 0

**Acción Requerida:**
- Agregar método `clean()` para validar:
  - `valor_libro_actual <= valor_adquisicion`
  - `fecha_adquisicion <= fecha_actual`
  - Valores monetarios >= 0

**Código Sugerido:**
```python
def clean(self):
    from django.core.exceptions import ValidationError
    from django.utils import timezone
    
    if self.valor_adquisicion < 0:
        raise ValidationError({'valor_adquisicion': 'El valor de adquisición no puede ser negativo'})
    
    if self.valor_libro_actual < 0:
        raise ValidationError({'valor_libro_actual': 'El valor libro no puede ser negativo'})
    
    if self.valor_libro_actual > self.valor_adquisicion:
        raise ValidationError({
            'valor_libro_actual': 'El valor libro no puede ser mayor al valor de adquisición'
        })
    
    if self.fecha_adquisicion > timezone.now().date():
        raise ValidationError({
            'fecha_adquisicion': 'La fecha de adquisición no puede ser futura'
        })
```

---

### 🟡 CALIDAD-003: Falta Validación en `Depreciacion.save()`
**Archivo:** `backend/activos/models.py`  
**Clase:** `Depreciacion`  
**Método:** `save()`  
**Severidad:** MEDIA  
**Estado:** Pendiente

**Descripción:**
El método `save()` de `Depreciacion` no valida la consistencia de los datos antes de actualizar el activo.

**Problemas Detectados:**
1. No valida que `valor_libro_nuevo` >= 0
2. No valida que `valor_libro_nuevo = valor_libro_anterior - monto` (con tolerancia para decimales)
3. No valida que la fecha no sea anterior a `fecha_adquisicion` del activo

**Acción Requerida:**
- Agregar validaciones en `save()` antes de actualizar el activo
- Agregar método `clean()` para validaciones de negocio

**Código Sugerido:**
```python
def clean(self):
    from django.core.exceptions import ValidationError
    from decimal import Decimal
    
    # Validar que valor_libro_nuevo >= 0
    if self.valor_libro_nuevo < 0:
        raise ValidationError({
            'valor_libro_nuevo': 'El valor libro nuevo no puede ser negativo'
        })
    
    # Validar consistencia: valor_libro_nuevo = valor_libro_anterior - monto
    expected_nuevo = self.valor_libro_anterior - self.monto
    if abs(self.valor_libro_nuevo - expected_nuevo) > Decimal('0.01'):
        raise ValidationError({
            'valor_libro_nuevo': f'El valor libro nuevo debe ser {expected_nuevo} (anterior - monto)'
        })
    
    # Validar que fecha >= fecha_adquisicion del activo
    if self.fecha < self.activo.fecha_adquisicion:
        raise ValidationError({
            'fecha': 'La fecha de depreciación no puede ser anterior a la fecha de adquisición'
        })

def save(self, *args, **kwargs):
    self.full_clean()  # Ejecutar validaciones
    super().save(*args, **kwargs)
    # ... resto del código
```

---

### 🟡 CALIDAD-004: Falta Manejo de Transacciones en `Depreciacion.save()`
**Archivo:** `backend/activos/models.py`  
**Clase:** `Depreciacion`  
**Método:** `save()`  
**Severidad:** MEDIA  
**Estado:** Pendiente

**Descripción:**
El método `save()` actualiza el activo sin usar transacciones, lo que puede dejar datos inconsistentes si falla.

**Código Actual:**
```python
def save(self, *args, **kwargs):
    """Actualiza el valor libro del activo al guardar"""
    super().save(*args, **kwargs)
    self.activo.valor_libro_actual = self.valor_libro_nuevo
    self.activo.save(update_fields=['valor_libro_actual', 'fecha_actualizacion'])
```

**Problema Detectado:**
- Si `activo.save()` falla, la depreciación queda guardada pero el activo no se actualiza
- No hay rollback automático

**Acción Requerida:**
- Envolver la actualización del activo en una transacción
- Considerar mover esta lógica a la vista donde ya hay transacción

**Código Sugerido:**
```python
from django.db import transaction

def save(self, *args, **kwargs):
    """Actualiza el valor libro del activo al guardar"""
    with transaction.atomic():
        super().save(*args, **kwargs)
        self.activo.valor_libro_actual = self.valor_libro_nuevo
        self.activo.save(update_fields=['valor_libro_actual', 'fecha_actualizacion'])
```

---

### 🟡 CALIDAD-005: Falta Validación de Empresa en Serializers
**Archivo:** `backend/activos/serializers.py`  
**Severidad:** MEDIA  
**Estado:** Pendiente

**Descripción:**
Los serializers no validan que el `tipo_activo` pertenezca a la misma empresa del usuario.

**Problema Detectado:**
- Un usuario podría asignar un tipo de activo de otra empresa
- No hay validación cruzada de empresa

**Acción Requerida:**
- Agregar validación en `ActivoFijoSerializer.validate_tipo_activo()` para verificar que pertenezca a la misma empresa
- Similar para otros campos relacionados con empresa

**Código Sugerido:**
```python
def validate_tipo_activo(self, value):
    request = self.context.get('request')
    if request and hasattr(request.user, 'empresa'):
        if value.empresa != request.user.empresa:
            raise serializers.ValidationError(
                'El tipo de activo debe pertenecer a su empresa'
            )
    return value
```

---

## Problemas de Seguridad (Media Prioridad)

### 🟡 SEGURIDAD-001: Permisos Insuficientes en `DepreciacionViewSet`
**Archivo:** `backend/activos/views.py`  
**Clase:** `DepreciacionViewSet`  
**Severidad:** MEDIA  
**Estado:** Pendiente

**Descripción:**
El `DepreciacionViewSet` permite crear/editar/eliminar a cualquier usuario autenticado, pero según el comentario debería ser solo lectura excepto para admins.

**Código Actual:**
```python
class DepreciacionViewSet(viewsets.ModelViewSet):
    """
    ViewSet para gestionar depreciaciones.
    Solo lectura excepto para admins.
    """
    queryset = Depreciacion.objects.select_related('activo').all()
    serializer_class = DepreciacionSerializer
    permission_classes = [IsAuthenticated]  # ❌ Permite todo a cualquier usuario autenticado
```

**Problema Detectado:**
- El comentario dice "Solo lectura excepto para admins" pero no está implementado
- Cualquier usuario puede crear/editar/eliminar depreciaciones directamente

**Acción Requerida:**
- Implementar permisos personalizados que permitan solo lectura a usuarios normales
- Permitir escritura solo a administradores
- O restringir la creación/edición de depreciaciones solo a través del endpoint `depreciar`

**Código Sugerido:**
```python
from rest_framework.permissions import IsAuthenticated, IsAdminUser
from rest_framework.decorators import action

class DepreciacionViewSet(viewsets.ReadOnlyModelViewSet):  # Solo lectura por defecto
    """
    ViewSet para gestionar depreciaciones.
    Solo lectura excepto para admins.
    """
    queryset = Depreciacion.objects.select_related('activo').all()
    serializer_class = DepreciacionSerializer
    permission_classes = [IsAuthenticated]
    
    def get_permissions(self):
        if self.action in ['create', 'update', 'destroy']:
            return [IsAdminUser()]  # Solo admins pueden crear/editar/eliminar
        return [IsAuthenticated()]
```

---

### 🟡 SEGURIDAD-002: Falta Validación de Permisos en Endpoints Personalizados
**Archivo:** `backend/activos/views.py`  
**Métodos:** `depreciar()`, `cambiar_estado()`  
**Severidad:** MEDIA  
**Estado:** Pendiente

**Descripción:**
Los endpoints personalizados `depreciar` y `cambiar_estado` no tienen validación de permisos específicos.

**Problema Detectado:**
- Cualquier usuario autenticado puede depreciar activos
- Cualquier usuario autenticado puede cambiar el estado de activos
- No hay control granular de permisos

**Acción Requerida:**
- Agregar decoradores de permisos a estos endpoints
- Considerar crear permisos personalizados para operaciones financieras críticas

---

## Problemas de Rendimiento (Baja Prioridad)

### 🔵 RENDIMIENTO-001: Consultas N+1 Potenciales
**Archivo:** `backend/activos/views.py`  
**Clase:** `ActivoFijoViewSet`  
**Severidad:** BAJA  
**Estado:** Pendiente

**Descripción:**
El queryset usa `select_related` pero faltan algunas relaciones importantes.

**Código Actual:**
```python
queryset = ActivoFijo.objects.select_related('tipo_activo', 'responsable').all()
```

**Problema Detectado:**
- Faltan relaciones como `empresa`, `usuario_creacion`, `usuario_modificacion`
- Esto puede causar consultas adicionales al serializar

**Acción Requerida:**
- Agregar más relaciones a `select_related`:
  ```python
  queryset = ActivoFijo.objects.select_related(
      'tipo_activo', 
      'responsable', 
      'empresa',
      'usuario_creacion',
      'usuario_modificacion'
  ).all()
  ```

---

### 🔵 RENDIMIENTO-002: Falta Índice en Campos Frecuentes
**Archivo:** `backend/activos/models.py`  
**Severidad:** BAJA  
**Estado:** Pendiente

**Descripción:**
Algunos campos que probablemente se filtren frecuentemente no tienen índices.

**Problemas Detectados:**
- `ActivoFijo.fecha_adquisicion` no tiene índice
- `Depreciacion.activo` podría beneficiarse de un índice compuesto con `fecha`

**Acción Requerida:**
- Agregar `db_index=True` a `fecha_adquisicion` en `ActivoFijo`
- Considerar índice compuesto en `Depreciacion` para `(activo, fecha)`

---

## Problemas de Documentación (Baja Prioridad)

### 🔵 DOC-001: Docstrings Incompletos
**Archivo:** `backend/activos/views.py`  
**Severidad:** BAJA  
**Estado:** Pendiente

**Descripción:**
Los métodos personalizados no documentan completamente su comportamiento y formato de respuesta.

**Métodos Afectados:**
- `por_estado()` - No documenta formato de respuesta
- `por_tipo()` - No documenta formato de respuesta
- `cambiar_estado()` - No documenta qué estados son válidos

**Acción Requerida:**
- Agregar docstrings completos con ejemplos de respuesta
- Documentar parámetros y valores de retorno

---

### 🔵 DOC-002: Falta Documentación de API
**Severidad:** BAJA  
**Estado:** Pendiente

**Descripción:**
No hay documentación OpenAPI/Swagger para los endpoints personalizados.

**Endpoints Afectados:**
- `POST /api/v1/activos/activos/{id}/depreciar/`
- `GET /api/v1/activos/activos/{id}/historial_depreciacion/`
- `POST /api/v1/activos/activos/{id}/cambiar_estado/`
- `GET /api/v1/activos/activos/por_estado/`
- `GET /api/v1/activos/activos/por_tipo/`

**Acción Requerida:**
- Agregar decoradores `@swagger_auto_schema` o documentación OpenAPI
- Documentar parámetros, respuestas y códigos de error

---

## Mejoras Recomendadas (Opcional)

### 💡 MEJORA-001: Agregar Validaciones de Modelo con `clean()`
**Descripción:** Implementar métodos `clean()` en todos los modelos para validaciones de negocio.

---

### 💡 MEJORA-002: Usar Señales (Signals) para Automatización
**Descripción:** Usar señales de Django para automatizar actualizaciones (ej: actualizar estado cuando `valor_libro_actual` llegue a 0).

---

### 💡 MEJORA-003: Separar Lógica de Negocio en Servicios
**Descripción:** Mover la lógica de depreciación a un servicio separado (`activos/services.py`) para mejor testabilidad.

---

### 💡 MEJORA-004: Definir Constantes
**Descripción:** Crear archivo `activos/constants.py` para definir constantes de estados y porcentajes máximos.

---

### 💡 MEJORA-005: Configurar Admin de Django
**Archivo:** `backend/activos/admin.py`  
**Descripción:** El archivo `admin.py` está vacío. Configurar la interfaz de administración para los modelos.

**Acción Requerida:**
- Registrar modelos en el admin
- Configurar list_display, list_filter, search_fields
- Agregar acciones personalizadas si es necesario

---

### 💡 MEJORA-006: Agregar Paginación Explícita
**Descripción:** Los ViewSets no definen paginación explícita, lo que puede causar problemas con grandes volúmenes.

**Acción Requerida:**
- Definir `pagination_class` en los ViewSets o usar la paginación global

---

### 💡 MEJORA-007: Agregar Logging
**Descripción:** Agregar logging para operaciones críticas (depreciaciones, cambios de estado).

---

## Cobertura de Tests

### 🧪 TEST-001: Tests Incompletos
**Archivo:** `backend/activos/tests.py`  
**Severidad:** MEDIA  
**Estado:** Pendiente

**Tests Faltantes:**
1. Tests para validaciones de negocio (valores negativos, rangos inválidos)
2. Tests para casos límite (fechas inválidas, valores extremos)
3. Tests para permisos y seguridad
4. Tests para cálculo de depreciación con diferentes escenarios
5. Tests para actualización automática del estado
6. Tests para validación de empresa en serializers
7. Tests para transacciones y rollback

**Acción Requerida:**
- Agregar tests para cada validación de negocio
- Agregar tests de integración para flujos completos
- Agregar tests de seguridad y permisos

---

## Matriz de Calidad

| Aspecto | Calificación | Estado | Prioridad |
|---------|-------------|--------|-----------|
| Funcionalidad | 6/10 | ⚠️ Bugs críticos | ALTA |
| Seguridad | 5/10 | ⚠️ Permisos básicos | MEDIA |
| Rendimiento | 7/10 | ✅ Bueno, mejorable | BAJA |
| Mantenibilidad | 6/10 | ⚠️ Falta documentación | MEDIA |
| Testabilidad | 5/10 | ⚠️ Tests incompletos | MEDIA |
| Documentación | 4/10 | ⚠️ Muy básica | BAJA |

**Calificación General:** 5.5/10

---

## Checklist de Resolución

### Alta Prioridad (Bloqueantes)
- [ ] CRÍTICO-001: Corregir error de sintaxis en `models.py` línea 85
- [ ] CRÍTICO-002: Corregir indentación del `@property` en línea 123
- [ ] CRÍTICO-003: Corregir bug en actualización de estado después de depreciación
- [ ] CRÍTICO-004: Corregir cálculo de depreciación (usar `valor_libro_actual`)

### Media Prioridad (Funcionalidad)
- [ ] CALIDAD-001: Agregar validaciones en `TipoActivo`
- [ ] CALIDAD-002: Agregar validaciones en `ActivoFijo`
- [ ] CALIDAD-003: Agregar validaciones en `Depreciacion.save()`
- [ ] CALIDAD-004: Mejorar manejo de transacciones
- [ ] CALIDAD-005: Agregar validación de empresa en serializers
- [ ] SEGURIDAD-001: Configurar permisos correctamente en `DepreciacionViewSet`
- [ ] SEGURIDAD-002: Agregar validación de permisos en endpoints personalizados
- [ ] TEST-001: Completar cobertura de tests

### Baja Prioridad (Mejoras)
- [ ] RENDIMIENTO-001: Optimizar consultas con `select_related`
- [ ] RENDIMIENTO-002: Agregar índices en campos frecuentes
- [ ] DOC-001: Mejorar docstrings
- [ ] DOC-002: Agregar documentación de API
- [ ] MEJORA-001: Implementar `clean()` en modelos
- [ ] MEJORA-002: Usar señales de Django
- [ ] MEJORA-003: Separar lógica en servicios
- [ ] MEJORA-004: Definir constantes
- [ ] MEJORA-005: Configurar admin
- [ ] MEJORA-006: Agregar paginación explícita
- [ ] MEJORA-007: Agregar logging

---

## Notas Adicionales

- Todos los problemas están documentados con código de ejemplo y sugerencias de solución
- Se recomienda resolver los problemas críticos primero antes de continuar con mejoras
- Después de resolver cada problema, actualizar el estado en este documento
- Considerar crear tests antes de implementar correcciones (TDD)

---

**Última Actualización:** 2025-01-27  
**Próxima Revisión:** Después de resolución de problemas críticos

