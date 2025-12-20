# Análisis QA - Módulo Caja

**Fecha:** 2025-01-27  
**Módulo:** `backend/caja`  
**Analista:** QA Team  
**Estado:** Pendiente de Resolución  
**Referencia:** [Guía Inicial](./Guia%20Inicial.md)

---

## Resumen Ejecutivo

El módulo de Caja gestiona las cajas físicas/lógicas, sesiones de caja (apertura/cierre) y movimientos de efectivo. El módulo presenta **problemas críticos** que deben ser resueltos urgentemente para cumplir con los estándares del proyecto y garantizar la integridad de datos en un entorno multiempresa.

**Calificación General:** 3.5/10

**Principales Problemas:**
- ❌ Falta completa de soporte multiempresa (campo `empresa` ausente)
- ❌ Validaciones de negocio inexistentes en modelos
- ❌ Falta de integración con sistema de permisos globales
- ❌ Lógica de negocio en vistas en lugar de servicios
- ❌ Campos de auditoría incompletos

---

## Problemas Críticos (Alta Prioridad - Bloqueantes)

### 🔴 CRÍTICO-001: Falta de Campo `empresa` en Modelo `Caja`
**Archivo:** `backend/caja/models.py`  
**Línea:** 6-23  
**Severidad:** CRÍTICA  
**Estado:** Pendiente  
**Principio Violado:** Multi-tenancy, SoC

**Descripción:**
El modelo `Caja` no tiene el campo `empresa`, lo cual es **OBLIGATORIO** para el sistema multiempresa. Sin este campo, no se puede filtrar por empresa y existe riesgo de acceso cruzado entre empresas.

**Código Actual:**
```python
class Caja(models.Model):
    nombre = models.CharField(max_length=100)
    descripcion = models.TextField(blank=True, null=True)
    activa = models.BooleanField(default=True)
    uuid = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)
    fecha_creacion = models.DateTimeField(auto_now_add=True)
    usuario_creacion = models.ForeignKey(...)
    # ❌ FALTA: campo empresa
```

**Problema Detectado:**
- No hay campo `empresa` para multi-tenancy
- No se puede filtrar cajas por empresa
- Violación de arquitectura multiempresa del sistema
- Riesgo de seguridad (acceso cruzado entre empresas)

**Código Requerido:**
```python
class Caja(models.Model):
    # Campo de empresa (OBLIGATORIO para multi-tenancy)
    empresa = models.ForeignKey(
        'empresas.Empresa',
        on_delete=models.PROTECT,
        related_name='cajas',
        db_index=True,  # Siempre indexar empresa
        null=True,
        blank=True
    )
    nombre = models.CharField(max_length=100)
    # ... resto de campos
```

**Acción Requerida:**
1. Agregar campo `empresa` al modelo `Caja`
2. Crear migración para agregar el campo
3. Actualizar `Meta` con `unique_together = ('empresa', 'nombre')` si aplica
4. Actualizar serializers para incluir `empresa`
5. Actualizar vistas para asignar empresa automáticamente

**Referencia:** Ver `backend/activos/models.py` línea 19-26 (TipoActivo.empresa)

---

### 🔴 CRÍTICO-002: Falta de Campo `empresa` en Modelo `SesionCaja`
**Archivo:** `backend/caja/models.py`  
**Línea:** 25-63  
**Severidad:** CRÍTICA  
**Estado:** Pendiente  
**Principio Violado:** Multi-tenancy, SoC

**Descripción:**
El modelo `SesionCaja` no tiene el campo `empresa`, lo cual es crítico para filtrar sesiones por empresa y garantizar el aislamiento de datos.

**Código Actual:**
```python
class SesionCaja(models.Model):
    caja = models.ForeignKey(Caja, on_delete=models.PROTECT, related_name='sesiones')
    usuario = models.ForeignKey(settings.AUTH_USER_MODEL, ...)
    # ❌ FALTA: campo empresa
```

**Problema Detectado:**
- No hay campo `empresa` para multi-tenancy
- No se puede filtrar sesiones por empresa
- Violación de arquitectura multiempresa

**Código Requerido:**
```python
class SesionCaja(models.Model):
    empresa = models.ForeignKey(
        'empresas.Empresa',
        on_delete=models.PROTECT,
        related_name='sesiones_caja',
        db_index=True,
        null=True,
        blank=True
    )
    caja = models.ForeignKey(Caja, on_delete=models.PROTECT, related_name='sesiones')
    # ... resto de campos
```

**Acción Requerida:**
1. Agregar campo `empresa` al modelo `SesionCaja`
2. Crear migración para agregar el campo
3. Actualizar lógica para asignar empresa automáticamente desde `caja.empresa`

---

### 🔴 CRÍTICO-003: Falta de Campo `empresa` en Modelo `MovimientoCaja`
**Archivo:** `backend/caja/models.py`  
**Línea:** 65-99  
**Severidad:** CRÍTICA  
**Estado:** Pendiente  
**Principio Violado:** Multi-tenancy, SoC

**Descripción:**
El modelo `MovimientoCaja` no tiene el campo `empresa`, lo cual es crítico para filtrar movimientos por empresa.

**Código Requerido:**
```python
class MovimientoCaja(models.Model):
    empresa = models.ForeignKey(
        'empresas.Empresa',
        on_delete=models.PROTECT,
        related_name='movimientos_caja',
        db_index=True,
        null=True,
        blank=True
    )
    sesion = models.ForeignKey(SesionCaja, ...)
    # ... resto de campos
```

**Acción Requerida:**
1. Agregar campo `empresa` al modelo `MovimientoCaja`
2. Crear migración para agregar el campo
3. Actualizar lógica para asignar empresa automáticamente desde `sesion.empresa`

---

### 🔴 CRÍTICO-004: Falta de Método `clean()` en Modelo `Caja`
**Archivo:** `backend/caja/models.py`  
**Línea:** 6-23  
**Severidad:** CRÍTICA  
**Estado:** Pendiente  
**Principio Violado:** Integridad de Datos, SRP

**Descripción:**
El modelo `Caja` no implementa el método `clean()` para validaciones de negocio. Según la guía inicial, **es OBLIGATORIO** implementar validaciones completas en `clean()` para garantizar la integridad de los datos.

**Código Actual:**
```python
class Caja(models.Model):
    # ... campos ...
    
    def __str__(self):
        return self.nombre
    # ❌ FALTA: método clean()
```

**Problema Detectado:**
- No hay validaciones de negocio en el modelo
- No se valida que el nombre sea único por empresa
- No se valida que la empresa exista y sea válida
- Riesgo de datos inconsistentes

**Código Requerido:**
```python
from django.core.exceptions import ValidationError

class Caja(models.Model):
    # ... campos ...
    
    def clean(self):
        """
        Validaciones de negocio para Caja.
        
        ⚠️ CRÍTICO: Este método es OBLIGATORIO y debe validar TODAS las reglas de negocio.
        La integridad de los datos depende de estas validaciones.
        """
        errors = {}
        
        # ========== VALIDACIONES DE RELACIONES ==========
        
        # Validar que caja pertenezca a la misma empresa del usuario (si se asigna)
        # Esta validación se hace principalmente en serializers
        
        # ========== VALIDACIONES DE UNICIDAD ==========
        
        # Validar unicidad de nombre por empresa
        if self.nombre and self.empresa:
            qs = type(self).objects.filter(nombre=self.nombre, empresa=self.empresa)
            if self.pk:
                qs = qs.exclude(pk=self.pk)
            if qs.exists():
                errors['nombre'] = 'Ya existe una caja con este nombre para esta empresa'
        
        # ========== LANZAR ERRORES ==========
        
        if errors:
            raise ValidationError(errors)
    
    def save(self, *args, **kwargs):
        """
        Guarda con validaciones completas.
        
        ⚠️ CRÍTICO: Siempre validar antes de guardar para garantizar integridad.
        """
        if 'update_fields' not in kwargs:
            self.full_clean()
        super().save(*args, **kwargs)
```

**Acción Requerida:**
1. Implementar método `clean()` completo con todas las validaciones
2. Implementar método `save()` que llame a `full_clean()`
3. Agregar `unique_together = ('empresa', 'nombre')` en `Meta`

**Referencia:** Ver `backend/activos/models.py` línea 48-68 (TipoActivo.clean())

---

### 🔴 CRÍTICO-005: Falta de Método `clean()` en Modelo `SesionCaja`
**Archivo:** `backend/caja/models.py`  
**Línea:** 25-63  
**Severidad:** CRÍTICA  
**Estado:** Pendiente  
**Principio Violado:** Integridad de Datos, SRP

**Descripción:**
El modelo `SesionCaja` no implementa el método `clean()` para validaciones de negocio críticas como montos no negativos, consistencia de fechas y validación de empresa.

**Código Requerido:**
```python
from django.core.exceptions import ValidationError
from django.utils import timezone

class SesionCaja(models.Model):
    # ... campos ...
    
    def clean(self):
        """
        Validaciones de negocio para SesionCaja.
        
        ⚠️ CRÍTICO: Estas validaciones garantizan la integridad de los datos.
        """
        errors = {}
        
        # ========== VALIDACIONES DE VALORES MONETARIOS ==========
        
        # Validar monto_apertura no negativo
        if self.monto_apertura is not None and self.monto_apertura < 0:
            errors['monto_apertura'] = 'El monto de apertura no puede ser negativo'
        
        # Validar monto_cierre_usuario no negativo (si existe)
        if self.monto_cierre_usuario is not None and self.monto_cierre_usuario < 0:
            errors['monto_cierre_usuario'] = 'El monto de cierre no puede ser negativo'
        
        # ========== VALIDACIONES DE FECHAS ==========
        
        # Validar que fecha_cierre no sea anterior a fecha_apertura
        if (self.fecha_cierre is not None and 
            self.fecha_apertura is not None and
            self.fecha_cierre < self.fecha_apertura):
            errors['fecha_cierre'] = 'La fecha de cierre no puede ser anterior a la fecha de apertura'
        
        # Validar que fecha_apertura no sea futura
        if self.fecha_apertura is not None:
            if self.fecha_apertura > timezone.now():
                errors['fecha_apertura'] = 'La fecha de apertura no puede ser futura'
        
        # ========== VALIDACIONES DE RELACIONES ==========
        
        # Validar que caja pertenezca a la misma empresa
        if (self.empresa is not None and 
            self.caja is not None and
            hasattr(self.caja, 'empresa') and
            self.caja.empresa is not None):
            if self.caja.empresa != self.empresa:
                errors['caja'] = 'La caja debe pertenecer a la misma empresa'
        
        # Validar que usuario pertenezca a la misma empresa (si aplica)
        if (self.empresa is not None and 
            self.usuario is not None and
            hasattr(self.usuario, 'empresa') and
            self.usuario.empresa is not None):
            if self.usuario.empresa != self.empresa:
                errors['usuario'] = 'El usuario debe pertenecer a la misma empresa'
        
        # ========== VALIDACIONES DE ESTADO ==========
        
        # Validar transiciones de estado
        if self.pk:  # Solo en updates
            estado_anterior = type(self).objects.get(pk=self.pk).estado
            transiciones_permitidas = {
                'ABIERTA': ['CERRADA'],
                'CERRADA': ['ARQUEADA'],
            }
            estados_permitidos = transiciones_permitidas.get(estado_anterior, [])
            if (self.estado != estado_anterior and 
                self.estado not in estados_permitidos):
                errors['estado'] = f'No se puede cambiar de {estado_anterior} a {self.estado}'
        
        # Validar que sesión cerrada tenga fecha_cierre
        if self.estado in ['CERRADA', 'ARQUEADA'] and not self.fecha_cierre:
            errors['fecha_cierre'] = 'La sesión cerrada debe tener fecha de cierre'
        
        # ========== LANZAR ERRORES ==========
        
        if errors:
            raise ValidationError(errors)
    
    def save(self, *args, **kwargs):
        """Guarda con validaciones completas"""
        if 'update_fields' not in kwargs:
            self.full_clean()
        super().save(*args, **kwargs)
```

**Acción Requerida:**
1. Implementar método `clean()` completo con todas las validaciones
2. Implementar método `save()` que llame a `full_clean()`
3. Probar todas las validaciones con tests

---

### 🔴 CRÍTICO-006: Falta de Método `clean()` en Modelo `MovimientoCaja`
**Archivo:** `backend/caja/models.py`  
**Línea:** 65-99  
**Severidad:** CRÍTICA  
**Estado:** Pendiente  
**Principio Violado:** Integridad de Datos, SRP

**Descripción:**
El modelo `MovimientoCaja` no implementa el método `clean()` para validaciones críticas como montos no negativos y validación de empresa.

**Código Requerido:**
```python
class MovimientoCaja(models.Model):
    # ... campos ...
    
    def clean(self):
        """
        Validaciones de negocio para MovimientoCaja.
        
        ⚠️ CRÍTICO: Estas validaciones garantizan la integridad de los datos.
        """
        errors = {}
        
        # ========== VALIDACIONES DE VALORES MONETARIOS ==========
        
        # Validar monto no negativo
        if self.monto is not None and self.monto <= 0:
            errors['monto'] = 'El monto debe ser mayor a cero'
        
        # ========== VALIDACIONES DE RELACIONES ==========
        
        # Validar que sesion pertenezca a la misma empresa
        if (self.empresa is not None and 
            self.sesion is not None and
            hasattr(self.sesion, 'empresa') and
            self.sesion.empresa is not None):
            if self.sesion.empresa != self.empresa:
                errors['sesion'] = 'La sesión debe pertenecer a la misma empresa'
        
        # Validar que sesion esté abierta (solo para creación)
        if self.sesion and self.sesion.estado != 'ABIERTA':
            if not self.pk:  # Solo en creación
                errors['sesion'] = 'No se pueden agregar movimientos a una sesión cerrada'
        
        # ========== LANZAR ERRORES ==========
        
        if errors:
            raise ValidationError(errors)
    
    def save(self, *args, **kwargs):
        """Guarda con validaciones completas"""
        if 'update_fields' not in kwargs:
            self.full_clean()
        super().save(*args, **kwargs)
```

**Acción Requerida:**
1. Implementar método `clean()` completo
2. Implementar método `save()` que llame a `full_clean()`
3. Remover lógica de validación del método `save()` actual (línea 96-99)

---

### 🔴 CRÍTICO-007: Campos de Auditoría Incompletos en Modelo `Caja`
**Archivo:** `backend/caja/models.py`  
**Línea:** 6-23  
**Severidad:** CRÍTICA  
**Estado:** Pendiente  
**Principio Violado:** Auditoría, Trazabilidad

**Descripción:**
El modelo `Caja` tiene campos de auditoría incompletos. Faltan `fecha_actualizacion` y `usuario_modificacion`.

**Código Actual:**
```python
class Caja(models.Model):
    uuid = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)
    fecha_creacion = models.DateTimeField(auto_now_add=True)
    usuario_creacion = models.ForeignKey(...)
    # ❌ FALTA: fecha_actualizacion
    # ❌ FALTA: usuario_modificacion
```

**Código Requerido:**
```python
class Caja(models.Model):
    uuid = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)
    fecha_creacion = models.DateTimeField(auto_now_add=True)
    fecha_actualizacion = models.DateTimeField(auto_now=True)
    usuario_creacion = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='cajas_creadas'
    )
    usuario_modificacion = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='cajas_modificadas'
    )
```

**Acción Requerida:**
1. Agregar `fecha_actualizacion` y `usuario_modificacion` a todos los modelos
2. Crear migración para agregar los campos
3. Actualizar serializers para incluir campos de auditoría como `read_only_fields`

---

### 🔴 CRÍTICO-008: Campos de Auditoría Incompletos en Modelo `SesionCaja`
**Archivo:** `backend/caja/models.py`  
**Línea:** 25-63  
**Severidad:** CRÍTICA  
**Estado:** Pendiente

**Descripción:**
El modelo `SesionCaja` tiene campos de auditoría incompletos. Faltan `fecha_actualizacion`, `usuario_creacion` y `usuario_modificacion`.

**Código Requerido:**
```python
class SesionCaja(models.Model):
    # ... campos existentes ...
    fecha_creacion = models.DateTimeField(auto_now_add=True)
    fecha_actualizacion = models.DateTimeField(auto_now=True)
    usuario_creacion = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='sesiones_caja_creadas'
    )
    usuario_modificacion = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='sesiones_caja_modificadas'
    )
```

**Acción Requerida:**
1. Agregar campos de auditoría faltantes
2. Crear migración
3. Actualizar vistas para asignar usuarios automáticamente

---

### 🔴 CRÍTICO-009: Campos de Auditoría Incompletos en Modelo `MovimientoCaja`
**Archivo:** `backend/caja/models.py`  
**Línea:** 65-99  
**Severidad:** CRÍTICA  
**Estado:** Pendiente

**Descripción:**
El modelo `MovimientoCaja` tiene campos de auditoría incompletos. Faltan `fecha_actualizacion` y `usuario_modificacion`.

**Acción Requerida:**
1. Agregar campos de auditoría faltantes
2. Crear migración
3. Actualizar vistas para asignar usuarios automáticamente

---

### 🔴 CRÍTICO-010: Vistas sin `EmpresaFilterMixin`
**Archivo:** `backend/caja/views.py`  
**Línea:** 18, 51, 177  
**Severidad:** CRÍTICA  
**Estado:** Pendiente  
**Principio Violado:** DRY, Multi-tenancy

**Descripción:**
Las vistas no usan `EmpresaFilterMixin` para filtrado automático por empresa. Esto es crítico para el sistema multiempresa.

**Código Actual:**
```python
class CajaViewSet(viewsets.ModelViewSet):
    queryset = Caja.objects.all()
    # ❌ FALTA: EmpresaFilterMixin
```

**Código Requerido:**
```python
from core.mixins import EmpresaFilterMixin

class CajaViewSet(EmpresaFilterMixin, viewsets.ModelViewSet):
    queryset = Caja.objects.select_related(
        'empresa',
        'usuario_creacion',
        'usuario_modificacion'
    ).all()
    # ... resto de configuración
```

**Vistas Afectadas:**
- `CajaViewSet` (línea 18)
- `SesionCajaViewSet` (línea 51)
- `MovimientoCajaViewSet` (línea 177)

**Acción Requerida:**
1. Agregar `EmpresaFilterMixin` a todas las vistas
2. Agregar `select_related()` para optimizar queries
3. Verificar que el filtrado funcione correctamente

**Referencia:** Ver `backend/activos/views.py` línea 42 (TipoActivoViewSet)

---

## Problemas Importantes (Media Prioridad)

### 🟡 IMPORTANTE-001: Falta de `select_related()` en Querysets
**Archivo:** `backend/caja/views.py`  
**Línea:** 20, 53, 179  
**Severidad:** IMPORTANTE  
**Estado:** Pendiente  
**Principio Violado:** Performance, Optimización

**Descripción:**
Los querysets no usan `select_related()` para optimizar consultas, lo que puede causar problemas de rendimiento (N+1 queries).

**Código Actual:**
```python
class SesionCajaViewSet(viewsets.ModelViewSet):
    queryset = SesionCaja.objects.all()  # ❌ Sin select_related
```

**Código Requerido:**
```python
class SesionCajaViewSet(EmpresaFilterMixin, viewsets.ModelViewSet):
    queryset = SesionCaja.objects.select_related(
        'caja',
        'usuario',
        'empresa',
        'usuario_creacion',
        'usuario_modificacion'
    ).all()
```

**Acción Requerida:**
1. Agregar `select_related()` a todos los querysets
2. Incluir todas las relaciones ForeignKey frecuentemente usadas

---

### 🟡 IMPORTANTE-002: Falta de Paginación Personalizada
**Archivo:** `backend/caja/views.py`  
**Severidad:** IMPORTANTE  
**Estado:** Pendiente  
**Principio Violado:** UX, Performance

**Descripción:**
Las vistas no definen paginación personalizada, lo que puede causar problemas de rendimiento con grandes volúmenes de datos.

**Código Requerido:**
```python
from rest_framework.pagination import PageNumberPagination

class CajaPagination(PageNumberPagination):
    page_size = 20
    page_size_query_param = 'page_size'
    max_page_size = 100

class CajaViewSet(EmpresaFilterMixin, viewsets.ModelViewSet):
    pagination_class = CajaPagination
    # ... resto de configuración
```

**Acción Requerida:**
1. Crear clases de paginación personalizadas para cada ViewSet
2. Configurar `page_size` apropiado según el tipo de datos

---

### 🟡 IMPORTANTE-003: Serializers sin Validación de Empresa
**Archivo:** `backend/caja/serializers.py`  
**Severidad:** IMPORTANTE  
**Estado:** Pendiente  
**Principio Violado:** Seguridad, Multi-tenancy

**Descripción:**
Los serializers no validan que las relaciones pertenezcan a la misma empresa del usuario, lo que puede permitir acceso cruzado entre empresas.

**Código Requerido:**
```python
class SesionCajaSerializer(serializers.ModelSerializer):
    # ... campos ...
    
    def validate_caja(self, value):
        """
        Valida que la caja pertenezca a la misma empresa del usuario.
        
        CRÍTICO: Siempre validar empresa en relaciones.
        """
        request = self.context.get('request')
        if request and hasattr(request.user, 'empresa'):
            user_empresa = request.user.empresa
            if value.empresa is not None and user_empresa is not None:
                if value.empresa != user_empresa:
                    raise serializers.ValidationError(
                        'La caja debe pertenecer a su empresa'
                    )
        return value
    
    def validate_sesion(self, value):
        """Valida que la sesión pertenezca a la misma empresa"""
        # Similar validación para MovimientoCajaSerializer
        return value
```

**Acción Requerida:**
1. Agregar `validate_caja()` en `SesionCajaSerializer`
2. Agregar `validate_sesion()` en `MovimientoCajaSerializer`
3. Probar validaciones con tests

---

### 🟡 IMPORTANTE-004: `perform_create()` y `perform_update()` Incompletos
**Archivo:** `backend/caja/views.py`  
**Línea:** 29, 66, 188  
**Severidad:** IMPORTANTE  
**Estado:** Pendiente  
**Principio Violado:** DRY, Auditoría

**Descripción:**
Los métodos `perform_create()` y `perform_update()` no asignan empresa y usuarios de auditoría correctamente.

**Código Actual:**
```python
def perform_create(self, serializer):
    serializer.save(usuario_creacion=self.request.user)
    # ❌ FALTA: asignar empresa
```

**Código Requerido:**
```python
def perform_create(self, serializer):
    serializer.save(
        empresa=self.request.user.empresa,
        usuario_creacion=self.request.user
    )

def perform_update(self, serializer):
    serializer.save(usuario_modificacion=self.request.user)
```

**Acción Requerida:**
1. Actualizar `perform_create()` en todas las vistas para asignar empresa
2. Agregar `perform_update()` en todas las vistas para asignar `usuario_modificacion`

---

### 🟡 IMPORTANTE-005: Lógica de Negocio en Vistas en lugar de Servicios
**Archivo:** `backend/caja/views.py`  
**Línea:** 102-120  
**Severidad:** IMPORTANTE  
**Estado:** Pendiente  
**Principio Violado:** SRP, SoC

**Descripción:**
La lógica de cierre de sesión está directamente en la vista (líneas 102-120), violando el principio SRP. Debería estar en un servicio.

**Código Actual:**
```python
@action(detail=True, methods=['post'])
def cerrar(self, request, pk=None):
    """Cierra una sesión de caja"""
    sesion = self.get_object()
    # ... lógica de negocio directamente en la vista (❌)
    ingresos = sesion.movimientos.filter(...).aggregate(...)
    egresos = sesion.movimientos.filter(...).aggregate(...)
    monto_sistema = ingresos - egresos
    # ... más lógica ...
```

**Código Requerido:**
```python
# Crear archivo: backend/caja/services.py
class SesionCajaService:
    @staticmethod
    def cerrar_sesion(sesion, monto_usuario, observaciones='', usuario=None):
        """
        Cierra una sesión de caja.
        
        Returns:
            Tuple (sesion_actualizada, error_message)
        """
        # Lógica de negocio aquí
        pass

# En views.py:
from .services import SesionCajaService

@action(detail=True, methods=['post'])
def cerrar(self, request, pk=None):
    """Cierra una sesión de caja"""
    sesion = self.get_object()
    serializer = CerrarSesionSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)
    
    sesion, error = SesionCajaService.cerrar_sesion(
        sesion=sesion,
        monto_usuario=serializer.validated_data['monto_cierre_usuario'],
        observaciones=serializer.validated_data.get('observaciones', ''),
        usuario=request.user
    )
    
    if error:
        return Response({'error': error}, status=status.HTTP_400_BAD_REQUEST)
    
    return Response(SesionCajaSerializer(sesion).data)
```

**Acción Requerida:**
1. Crear archivo `services.py`
2. Mover lógica de negocio de vistas a servicios
3. Usar transacciones (`transaction.atomic()`) en servicios
4. Retornar tuplas `(resultado, error)` para manejo consistente

---

### 🟡 IMPORTANTE-006: Método `cerrar_sesion()` en Modelo
**Archivo:** `backend/caja/models.py`  
**Línea:** 58-63  
**Severidad:** IMPORTANTE  
**Estado:** Pendiente  
**Principio Violado:** SRP

**Descripción:**
El método `cerrar_sesion()` está en el modelo, pero debería estar en un servicio según el principio SRP (modelos solo manejan datos y validaciones básicas).

**Código Actual:**
```python
def cerrar_sesion(self, monto_usuario):
    self.fecha_cierre = timezone.now()
    self.monto_cierre_usuario = monto_usuario
    self.diferencia = self.monto_cierre_usuario - self.monto_cierre_sistema
    self.estado = 'CERRADA'
    self.save()
```

**Acción Requerida:**
1. Mover `cerrar_sesion()` a `SesionCajaService`
2. Remover método del modelo
3. Actualizar vistas para usar el servicio

---

### 🟡 IMPORTANTE-007: Falta de Archivo `constants.py`
**Archivo:** No existe  
**Severidad:** IMPORTANTE  
**Estado:** Pendiente  
**Principio Violado:** DRY

**Descripción:**
No existe archivo `constants.py` para centralizar constantes como estados y tipos de movimiento.

**Código Requerido:**
```python
# backend/caja/constants.py
"""
Constantes para el módulo Caja
"""

# Estados de SesionCaja
ESTADO_ABIERTA = 'ABIERTA'
ESTADO_CERRADA = 'CERRADA'
ESTADO_ARQUEADA = 'ARQUEADA'

ESTADO_CHOICES = (
    (ESTADO_ABIERTA, 'Abierta'),
    (ESTADO_CERRADA, 'Cerrada'),
    (ESTADO_ARQUEADA, 'Arqueada'),
)

# Tipos de MovimientoCaja
TIPO_VENTA = 'VENTA'
TIPO_INGRESO_MANUAL = 'INGRESO_MANUAL'
TIPO_RETIRO_MANUAL = 'RETIRO_MANUAL'
TIPO_GASTO_MENOR = 'GASTO_MENOR'
TIPO_APERTURA = 'APERTURA'
TIPO_CIERRE = 'CIERRE'

TIPO_MOVIMIENTO_CHOICES = (
    (TIPO_VENTA, 'Venta (Cobro)'),
    (TIPO_INGRESO_MANUAL, 'Ingreso Manual'),
    (TIPO_RETIRO_MANUAL, 'Retiro Manual'),
    (TIPO_GASTO_MENOR, 'Gasto Menor'),
    (TIPO_APERTURA, 'Monto Apertura'),
    (TIPO_CIERRE, 'Retiro por Cierre'),
)

# Tipos de movimiento que son ingresos
TIPOS_INGRESO = [TIPO_VENTA, TIPO_INGRESO_MANUAL, TIPO_APERTURA]

# Tipos de movimiento que son egresos
TIPOS_EGRESO = [TIPO_RETIRO_MANUAL, TIPO_GASTO_MENOR, TIPO_CIERRE]
```

**Acción Requerida:**
1. Crear archivo `constants.py`
2. Mover constantes de modelos a `constants.py`
3. Importar constantes en modelos y servicios

---

### 🟡 IMPORTANTE-008: Falta de Índices en Campos Importantes
**Archivo:** `backend/caja/models.py`  
**Severidad:** IMPORTANTE  
**Estado:** Pendiente  
**Principio Violado:** Performance

**Descripción:**
Faltan índices en campos frecuentemente consultados como `estado`, `fecha_apertura`, `tipo_movimiento`.

**Código Requerido:**
```python
class SesionCaja(models.Model):
    # ... campos ...
    
    class Meta:
        # ... opciones existentes ...
        indexes = [
            models.Index(fields=['empresa', 'estado']),
            models.Index(fields=['empresa', 'fecha_apertura']),
            models.Index(fields=['caja', 'estado']),
        ]

class MovimientoCaja(models.Model):
    # ... campos ...
    
    class Meta:
        # ... opciones existentes ...
        indexes = [
            models.Index(fields=['empresa', 'tipo_movimiento']),
            models.Index(fields=['empresa', 'fecha']),
            models.Index(fields=['sesion', 'tipo_movimiento']),
        ]
```

**Acción Requerida:**
1. Agregar índices en `Meta` de modelos
2. Crear migración para agregar índices
3. Verificar rendimiento después de agregar índices

---

## Problemas Menores (Baja Prioridad)

### 🟢 MENOR-001: Falta de Archivo `permissions.py`
**Archivo:** No existe  
**Severidad:** MENOR  
**Estado:** Pendiente

**Descripción:**
No existe archivo `permissions.py` para permisos personalizados. Aunque no es crítico, sería útil para acciones específicas como cerrar sesión o arquear.

**Código Requerido:**
```python
# backend/caja/permissions.py
from core.permissions import BaseEmpresaPermission

class CanCerrarSesion(BaseEmpresaPermission):
    def __init__(self):
        super().__init__(
            permission_codename='caja.cerrar_sesion',
            message='No tiene permiso para cerrar sesiones de caja.'
        )

class CanArquearSesion(BaseEmpresaPermission):
    def __init__(self):
        super().__init__(
            permission_codename='caja.arquear_sesion',
            message='No tiene permiso para arquear sesiones de caja.'
        )
```

**Acción Requerida:**
1. Crear archivo `permissions.py` si se necesitan permisos personalizados
2. Definir permisos en `Meta.permissions` de modelos
3. Aplicar permisos en acciones críticas con `@action(permission_classes=[...])`

---

### 🟢 MENOR-002: Falta de Archivo `admin.py`
**Archivo:** No existe  
**Severidad:** MENOR  
**Estado:** Pendiente

**Descripción:**
No existe archivo `admin.py` para configuración del admin de Django.

**Código Requerido:**
```python
# backend/caja/admin.py
from django.contrib import admin
from .models import Caja, SesionCaja, MovimientoCaja

@admin.register(Caja)
class CajaAdmin(admin.ModelAdmin):
    list_display = ['nombre', 'empresa', 'activa', 'fecha_creacion']
    list_filter = ['activa', 'empresa', 'fecha_creacion']
    search_fields = ['nombre', 'descripcion']
    ordering = ['nombre']
    readonly_fields = ['uuid', 'fecha_creacion', 'fecha_actualizacion']

# Similar para SesionCaja y MovimientoCaja
```

**Acción Requerida:**
1. Crear archivo `admin.py` con configuración completa
2. Configurar `list_display`, `list_filter`, `search_fields` para cada modelo

---

### 🟢 MENOR-003: Falta de Archivo `signals.py`
**Archivo:** No existe  
**Severidad:** MENOR  
**Estado:** Pendiente

**Descripción:**
No existe archivo `signals.py` para automatizar comportamientos como actualizar `monto_cierre_sistema` cuando se crean movimientos.

**Código Requerido:**
```python
# backend/caja/signals.py
from django.db.models.signals import post_save
from django.dispatch import receiver
from .models import MovimientoCaja

@receiver(post_save, sender=MovimientoCaja)
def actualizar_monto_cierre_sistema(sender, instance, **kwargs):
    """Actualiza monto_cierre_sistema en la sesión cuando se crea un movimiento"""
    if instance.sesion:
        # Recalcular monto_cierre_sistema
        # (Lógica de cálculo)
        pass
```

**Acción Requerida:**
1. Crear archivo `signals.py` si se necesitan automatizaciones
2. Registrar señales en `apps.py`

---

### 🟢 MENOR-004: Tests Incompletos
**Archivo:** `backend/caja/tests.py`  
**Severidad:** MENOR  
**Estado:** Pendiente

**Descripción:**
Los tests no cubren validaciones de modelos, filtrado por empresa, ni permisos personalizados.

**Tests Faltantes:**
- Tests de validaciones de modelos (`clean()`)
- Tests de filtrado por empresa
- Tests de permisos personalizados
- Tests de servicios (si se crean)
- Tests de transiciones de estado

**Acción Requerida:**
1. Agregar tests de validaciones
2. Agregar tests de filtrado por empresa
3. Agregar tests de servicios

---

### 🟢 MENOR-005: Comentario TODO en `MovimientoCaja.save()`
**Archivo:** `backend/caja/models.py`  
**Línea:** 96-99  
**Severidad:** MENOR  
**Estado:** Pendiente

**Descripción:**
Hay un comentario TODO en el método `save()` que indica que la lógica debería estar en signals o servicios.

**Código Actual:**
```python
def save(self, *args, **kwargs):
    super().save(*args, **kwargs)
    # Actualizar monto sistema en la sesión si es necesario
    # (Lógica simplificada, idealmente usar signals o métodos de servicio)
```

**Acción Requerida:**
1. Implementar la lógica en signals o servicios
2. Remover comentario TODO

---

## Checklist de Cumplimiento con Guía Inicial

### Estructura Básica
- [x] `__init__.py` existe
- [x] `apps.py` existe
- [x] `models.py` existe
- [x] `serializers.py` existe
- [x] `views.py` existe
- [x] `urls.py` existe
- [x] `tests.py` existe
- [ ] `admin.py` existe
- [ ] `permissions.py` existe
- [ ] `services.py` existe (recomendado)
- [ ] `constants.py` existe (recomendado)
- [ ] `signals.py` existe (recomendado)

### Migraciones
- [x] Migración inicial existe
- [ ] Verificar sintaxis (`python manage.py makemigrations --dry-run`)
- [ ] Verificar plan de migración (`python manage.py migrate --plan`)
- [ ] Verificar que se puede aplicar (`python manage.py migrate`)
- [ ] Verificar dependencias están correctas
- [ ] Incluir índices en migraciones

### Modelos
- [ ] Campo `empresa` con `db_index=True` en TODOS los modelos
- [ ] Campos de auditoría completos (uuid, fechas, usuarios) en TODOS los modelos
- [ ] Método `clean()` COMPLETO con TODAS las validaciones en TODOS los modelos
  - [ ] Validar valores numéricos (no negativos, rangos)
  - [ ] Validar fechas (no futuras, consistencia)
  - [ ] Validar relaciones (empresa, integridad referencial)
  - [ ] Validar consistencia entre campos relacionados
  - [ ] Validar reglas de negocio específicas
  - [ ] Validar transiciones de estado (si aplica)
- [ ] `save()` con `full_clean()` en TODOS los modelos
- [ ] Método `__str__()` descriptivo (✅ Ya existe)
- [ ] `Meta` con `verbose_name`, `ordering`, `indexes` en TODOS los modelos
- [ ] `Meta` con `unique_together` si aplica (garantizar unicidad)
- [ ] `related_name` descriptivo en ForeignKeys (✅ Ya existe)
- [ ] `on_delete` apropiado (PROTECT para críticos) (✅ Ya existe)

### Vistas
- [ ] Usar `EmpresaFilterMixin` en TODAS las vistas
- [ ] Usar `select_related()` en querysets de TODAS las vistas
- [ ] Implementar paginación personalizada en TODAS las vistas
- [ ] `filterset_fields`, `search_fields`, `ordering_fields` (✅ Ya existe)
- [ ] `perform_create()` y `perform_update()` completos en TODAS las vistas
- [ ] Documentar endpoints con docstrings (✅ Ya existe)

### Serializers
- [ ] Validar empresa en relaciones (`validate_[campo]()`) en TODOS los serializers
- [ ] `read_only_fields` para auditoría (✅ Parcialmente implementado)
- [ ] Serializer separado para listado si es necesario (✅ Ya existe)

### Permisos
- [ ] Usar `BaseEmpresaPermission` (si hay permisos personalizados)
- [ ] Definir permisos en `Meta.permissions` del modelo

### Servicios (Opcional pero Recomendado)
- [ ] Crear `services.py` si hay lógica de negocio compleja
- [ ] Usar transacciones para operaciones múltiples
- [ ] Retornar tuplas `(resultado, error)`
- [ ] Usar logging

### Constantes (Opcional pero Recomendado)
- [ ] Crear `constants.py` con constantes centralizadas
- [ ] Estados, valores por defecto, tolerancias

### Señales (Opcional)
- [ ] Crear `signals.py` si hay automatizaciones
- [ ] Registrar en `apps.py`

### Tests
- [x] Tests básicos existen
- [ ] Tests de validaciones
- [ ] Tests de filtrado por empresa
- [ ] Tests de permisos (si hay permisos personalizados)
- [ ] Tests de servicios (si hay servicios)

### Admin
- [ ] `list_display` con campos importantes
- [ ] `list_filter` útil
- [ ] `search_fields` configurado
- [ ] `fieldsets` organizados

### Principios de Diseño (Verificar en Todo el Módulo)
- [ ] **DRY**: No hay código duplicado (usar clases base, mixins, servicios)
- [ ] **KISS**: Código simple y directo, sin sobre-ingeniería
- [ ] **SRP**: Cada clase/módulo tiene una sola responsabilidad
- [ ] **SoC**: Capas separadas (modelos, vistas, servicios, serializers)
- [ ] **YAGNI**: Solo funcionalidad necesaria, nada "por si acaso"

---

## Plan de Acción Recomendado

### Fase 1: Correcciones Críticas (Bloqueantes)
**Tiempo estimado:** 2-3 días

1. **Agregar campo `empresa` a todos los modelos**
   - Crear migraciones
   - Actualizar modelos
   - Actualizar serializers
   - Actualizar vistas

2. **Implementar `clean()` completo en todos los modelos**
   - Validaciones de valores
   - Validaciones de fechas
   - Validaciones de relaciones
   - Validaciones de estado

3. **Agregar `full_clean()` en `save()` de todos los modelos**

4. **Completar campos de auditoría**
   - Agregar `fecha_actualizacion` y `usuario_modificacion`
   - Crear migraciones

5. **Agregar `EmpresaFilterMixin` a todas las vistas**

6. **Agregar validación de empresa en serializers**

### Fase 2: Mejoras Importantes
**Tiempo estimado:** 1-2 días

7. **Crear `services.py` para lógica de negocio**
   - Mover lógica de cierre de sesión
   - Mover lógica de cálculo de montos

8. **Optimizar querysets con `select_related()`**

9. **Agregar paginación personalizada**

10. **Crear `constants.py`**

11. **Agregar índices en campos importantes**

### Fase 3: Mejoras Menores
**Tiempo estimado:** 1 día

12. **Crear `permissions.py`** (si se necesitan permisos personalizados)

13. **Crear `admin.py`**

14. **Crear `signals.py`** (si se necesitan automatizaciones)

15. **Mejorar tests**

---

## Referencias

- [Guía Inicial](./Guia%20Inicial.md) - Estándares y mejores prácticas
- `backend/activos/` - Módulo de referencia para implementación correcta
- [Manejo de Permisos Globales](./Manejo%20de%20permisos%20globales.md) - Sistema de permisos

---

## Conclusión

El módulo de Caja requiere **refactorización completa** para cumplir con los estándares del proyecto. Los problemas críticos relacionados con multi-tenancy y validaciones deben resolverse antes de considerar el módulo como estable para producción.

**Prioridad:** 🔴 CRÍTICA  
**Esfuerzo Estimado:** 4-6 días de desarrollo  
**Riesgo:** ALTO (sin correcciones críticas, el módulo no es seguro para producción)

---

**Última Actualización:** 2025-01-27  
**Versión:** 1.0  
**Mantenido por:** QA Team
