# Manejo de Permisos Globales - Solución Genérica

**Fecha:** 2025-01-27
**Alcance:** Sistema completo - Todos los módulos
**Tipo:** Infraestructura Global
**Prioridad:** Media
**Estado:** ✅ IMPLEMENTACIÓN COMPLETADA
**Versión Django:** 6.0
**Versión Django REST Framework:** Compatible con DRF estándar

---

## 📋 Estado Actual y Última Actividad

**Última Actualización:** 2025-01-28
**Último Trabajo Realizado:** ✅ Implementación completa de todas las fases

**Estado de Implementación:**
- ✅ Fase 1: Infraestructura Base - `core/permissions/` creado
- ✅ Fase 2: Módulos Refactorizados - `activos/`, `usuarios/`
- ✅ Fase 3: Otros Módulos - `core/views.py`
- ✅ Fase 4: Utilidades - `utils.py` con helpers, decoradores y funciones de testing

**Archivos Creados/Modificados:**
- `backend/core/permissions/__init__.py` - Exports completos
- `backend/core/permissions/base.py` - Clases base genéricas
- `backend/core/permissions/mixins.py` - Mixins reutilizables
- `backend/core/permissions/utils.py` - Utilidades (~350 líneas)
- `backend/core/permissions/tests.py` - 63 tests
- `backend/activos/permissions.py` - Refactorizado (reducción 46%)
- `backend/usuarios/permissions.py` - Refactorizado con mixins
- `backend/core/views.py` - Refactorizado con AdminStaffMixin

**Commits Realizados:**
- `feat: Implement global permissions infrastructure (core/permissions)`
- `refactor: Update usuarios/permissions.py to use core mixins`
- `feat: Add permissions utilities module (Phase 4)`

**Métricas:**
- Total tests de permisos: 63
- Reducción de código en activos: ~46%
- Cobertura de funcionalidades: 100%

---

## Resumen Ejecutivo

Este documento describe la creación de una **infraestructura global y genérica** de permisos que elimine código duplicado en **todos los módulos** del sistema y proporcione un sistema centralizado, reutilizable y consistente de manejo de permisos.

**Objetivo:** Crear una arquitectura de permisos unificada y genérica que:
- Elimine duplicación de código en todos los módulos
- Proporcione clases base reutilizables para cualquier módulo
- Facilite el mantenimiento y extensión del sistema de permisos
- Garantice consistencia en la validación de permisos en todo el sistema

**Alcance:** Aplicable a **todos los módulos** del sistema (activos, usuarios, compras, ventas, inventario, etc.)

---

## Problema Actual

### Código Duplicado en Todo el Sistema

Se ha identificado un patrón de código duplicado en múltiples módulos del sistema:

**Módulos con código duplicado identificado:**
- `activos/permissions.py` - `CanDepreciarActivo`, `CanCambiarEstadoActivo`, `CanVerProyeccion`
- `usuarios/permissions.py` - `IsAdminOrSameEmpresa` y otros permisos
- Otros módulos con permisos personalizados

**Patrón común repetido en múltiples módulos:**
1. Verificación de autenticación (`if not request.user.is_authenticated`)
2. Verificación de superusuario/staff (`if user.is_superuser or user.is_staff`)
3. Verificación de permiso específico (`user.has_perm('app.action_model')`)
4. Validación de empresa en `has_object_permission` (`obj.empresa == user.empresa`)

**Impacto Global:**
- Cientos de líneas de código duplicado en todo el sistema
- Dificultad para mantener consistencia entre módulos
- Alto riesgo de errores al modificar lógica común
- Dificultad para agregar nuevas validaciones globales (ej: IP, ubicación, horario)
- Tiempo perdido al crear nuevos permisos desde cero

---

## Alcance del Proyecto

### Fase 1: Crear Infraestructura Global Base (Alta Prioridad)

**Objetivo:** Crear clases base genéricas y reutilizables para **cualquier módulo** del sistema.

**Componentes a crear en `core/permissions/`:**

1. **`base.py`** - Clases base genéricas para permisos
   - `BaseEmpresaPermission` - Permiso genérico con validación de empresa (aplicable a cualquier módulo)
   - `BaseModelPermission` - Permiso genérico para modelos específicos
   - `BaseActionPermission` - Permiso genérico para acciones personalizadas
   - `BaseReadOnlyPermission` - Permiso genérico para operaciones de solo lectura

2. **`mixins.py`** - Mixins genéricos reutilizables
   - `EmpresaValidationMixin` - Validación de empresa (genérico)
   - `AdminStaffMixin` - Verificación de admin/staff (genérico)
   - `PermissionCheckMixin` - Verificación de permisos específicos (genérico)
   - `OwnerValidationMixin` - Validación de propiedad (genérico)

3. **`utils.py`** - Utilidades genéricas
   - Helpers para verificación de permisos
   - Funciones de utilidad para testing
   - Decoradores reutilizables

4. **Documentación global**
   - Guía de uso para todos los módulos
   - Ejemplos de implementación genéricos
   - Guía de migración universal

### Fase 2: Refactorizar Módulos Existentes (Alta Prioridad)

**Objetivo:** Refactorizar permisos existentes en todos los módulos usando las clases base genéricas.

**Módulos a refactorizar (prioridad):**

1. **`activos/permissions.py`** (Alta prioridad - caso de uso identificado)
   - Migrar `CanDepreciarActivo` → `BaseEmpresaPermission`
   - Migrar `CanCambiarEstadoActivo` → `BaseEmpresaPermission`
   - Migrar `CanVerProyeccion` → `BaseEmpresaPermission`

2. **`usuarios/permissions.py`** (Alta prioridad)
   - Refactorizar `IsAdminOrSameEmpresa` → `BaseEmpresaPermission`
   - Revisar otros permisos personalizados

3. **Otros módulos** (Media prioridad - según auditoría)
   - `compras/`, `ventas/`, `inventario/`, `productos/`, etc.
   - Identificar y refactorizar permisos personalizados

**Estrategia:** Migración gradual módulo por módulo, manteniendo compatibilidad.

### Fase 3: Establecer Estándares y Mejores Prácticas (Media Prioridad)

**Objetivo:** Documentar y establecer estándares para uso futuro.

**Tareas:**
- Crear guía de mejores prácticas
- Establecer convenciones de nomenclatura
- Crear plantillas para nuevos permisos
- Documentar patrones comunes

### Fase 4: Utilidades Avanzadas y Optimizaciones (Baja Prioridad)

**Objetivo:** Crear utilidades avanzadas y optimizaciones.

**Componentes:**
- Decoradores avanzados para permisos
- Helpers para testing de permisos
- Caché de verificación de permisos (si es necesario)
- Logging y auditoría de permisos

---

## Beneficios Esperados

### 1. Reducción de Código Duplicado (Global)

**Antes:**
- Cientos de líneas de código duplicado en múltiples módulos
- Lógica repetida en cada módulo que implementa permisos
- Cada nuevo permiso requiere escribir ~40-50 líneas desde cero

**Después:**
- ~100-150 líneas de código base genérico reutilizable en `core/permissions/`
- Lógica común centralizada para todo el sistema
- Nuevos permisos requieren solo 5-10 líneas de configuración
- **Reducción estimada: 60-70% de código en cada módulo**
- **Reducción total estimada: 500+ líneas de código duplicado eliminadas**

### 2. Mantenibilidad Mejorada

**Beneficios:**
- ✅ Cambios en lógica común se hacen en un solo lugar
- ✅ Consistencia garantizada entre todos los permisos
- ✅ Más fácil agregar nuevas validaciones globales
- ✅ Código más legible y fácil de entender

**Ejemplo:**
Si necesitamos agregar validación de IP o ubicación, solo se modifica la clase base.

### 3. Facilidad de Extensión (Global)

**Beneficios:**
- ✅ Crear nuevos permisos en **cualquier módulo** es más rápido (solo configurar parámetros)
- ✅ Menos código para escribir y mantener en todos los módulos
- ✅ Patrón consistente en **todo el sistema**
- ✅ Nuevos desarrolladores pueden crear permisos rápidamente sin conocer detalles internos
- ✅ Fácil agregar nuevas validaciones globales (ej: IP, ubicación) que se aplican automáticamente

**Ejemplo:**
Crear un nuevo permiso en cualquier módulo toma 5-10 líneas en lugar de 40-50.

### 4. Testabilidad Mejorada

**Beneficios:**
- ✅ Tests de la clase base cubren todos los permisos derivados
- ✅ Tests más simples y enfocados
- ✅ Menos tests duplicados

### 5. Documentación Centralizada

**Beneficios:**
- ✅ Documentación en un solo lugar
- ✅ Ejemplos claros de uso
- ✅ Guías de migración disponibles

### 6. Seguridad Mejorada

**Beneficios:**
- ✅ Validaciones consistentes en todo el sistema
- ✅ Menos riesgo de errores por código duplicado
- ✅ Auditoría más fácil (lógica centralizada)

---

## Directrices de Implementación

### Principios de Diseño

#### 1. DRY (Don't Repeat Yourself)
- **Regla:** Toda lógica común debe estar en clases base o mixins
- **Aplicación:** Si 3+ clases tienen la misma lógica, crear clase base

#### 2. Single Responsibility
- **Regla:** Cada clase de permiso debe tener una responsabilidad clara
- **Aplicación:** Separar validación de empresa, admin/staff, y permisos específicos

#### 3. Open/Closed Principle
- **Regla:** Abierto para extensión, cerrado para modificación
- **Aplicación:** Clases base extensibles sin modificar código existente

#### 4. Composition over Inheritance
- **Regla:** Preferir composición (mixins) cuando sea apropiado
- **Aplicación:** Usar mixins para funcionalidades opcionales

### Estructura de Archivos Propuesta

```
backend/
├── core/
│   ├── permissions/          # INFRAESTRUCTURA GLOBAL
│   │   ├── __init__.py       # Exports de clases base genéricas
│   │   ├── base.py           # Clases base genéricas (aplicables a cualquier módulo)
│   │   ├── mixins.py         # Mixins genéricos reutilizables
│   │   └── utils.py          # Utilidades genéricas y helpers
│   └── ...
├── activos/
│   ├── permissions.py        # Permisos específicos usando clases base genéricas
│   └── ...
├── usuarios/
│   ├── permissions.py        # Permisos específicos usando clases base genéricas
│   └── ...
├── compras/
│   ├── permissions.py        # Permisos específicos usando clases base genéricas
│   └── ...
├── ventas/
│   ├── permissions.py        # Permisos específicos usando clases base genéricas
│   └── ...
└── [cualquier otro módulo]/
    ├── permissions.py        # Todos usan las mismas clases base genéricas
    └── ...
```

**Nota:** Todos los módulos importan y usan las clases base genéricas de `core/permissions/`

### Convenciones de Nomenclatura

#### Clases Base
- Prefijo: `Base` (ej: `BaseEmpresaPermission`)
- Sufijo: `Permission` (ej: `BaseModelPermission`)

#### Mixins
- Sufijo: `Mixin` (ej: `EmpresaValidationMixin`)

#### Permisos Específicos
- Prefijo: `Can` para acciones (ej: `CanDepreciarActivo`)
- Prefijo: `Is` para estados/roles (ej: `IsActivoResponsable`)

### Patrones de Uso

#### Patrón 1: Permiso Simple con Empresa (Aplicable a Cualquier Módulo)

```python
# Ejemplo en activos/permissions.py
from core.permissions.base import BaseEmpresaPermission

class CanDepreciarActivo(BaseEmpresaPermission):
    """Permiso para registrar depreciaciones"""
    def __init__(self):
        super().__init__(
            permission_codename='activos.depreciar_activofijo',
            message='No tiene permiso para registrar depreciaciones.'
        )

# Ejemplo en compras/permissions.py (mismo patrón, diferente módulo)
class CanAprobarCompra(BaseEmpresaPermission):
    """Permiso para aprobar compras"""
    def __init__(self):
        super().__init__(
            permission_codename='compras.aprobar_compra',
            message='No tiene permiso para aprobar compras.'
        )

# Ejemplo en ventas/permissions.py (mismo patrón, diferente módulo)
class CanAnularVenta(BaseEmpresaPermission):
    """Permiso para anular ventas"""
    def __init__(self):
        super().__init__(
            permission_codename='ventas.anular_venta',
            message='No tiene permiso para anular ventas.'
        )
```

**Ventaja:** Mismo código base, aplicable a cualquier módulo del sistema.

#### Patrón 2: Permiso con Validación Personalizada (Extensible)

```python
from core.permissions.base import BaseEmpresaPermission

class CanCambiarEstadoActivo(BaseEmpresaPermission):
    """Permiso con validación adicional de transiciones"""
    def __init__(self):
        super().__init__(
            permission_codename='activos.cambiar_estado_activofijo',
            message='No tiene permiso para cambiar estado.'
        )
    
    def has_object_permission(self, request, view, obj):
        # Validación base (empresa, permiso) - GENÉRICA
        if not super().has_object_permission(request, view, obj):
            return False
        
        # Validación personalizada adicional - ESPECÍFICA DEL MÓDULO
        # (ej: verificar transiciones de estado permitidas)
        return self._validate_state_transition(obj, request.data.get('estado'))
```

**Ventaja:** Base genérica + extensión específica del módulo.

#### Patrón 3: Permiso con Mixins (Composición Flexible)

```python
from core.permissions.mixins import EmpresaValidationMixin, AdminStaffMixin
from rest_framework import permissions

class CustomPermission(EmpresaValidationMixin, AdminStaffMixin, permissions.BasePermission):
    """Permiso personalizado usando mixins genéricos"""
    permission_codename = 'app.action_model'
    
    def has_permission(self, request, view):
        if not self._is_admin_or_staff(request.user):
            return request.user.has_perm(self.permission_codename)
        return True
```

**Ventaja:** Composición flexible de funcionalidades genéricas.

#### Patrón 4: Permiso para Cualquier Modelo (Completamente Genérico)

```python
from core.permissions.base import BaseEmpresaPermission

# Usable en cualquier módulo sin modificar la clase base
class CanEditModel(BaseEmpresaPermission):
    """Permiso genérico para editar cualquier modelo"""
    def __init__(self, app_label, model_name):
        super().__init__(
            permission_codename=f'{app_label}.change_{model_name}',
            message=f'No tiene permiso para editar {model_name}.'
        )
```

### Guía de Migración (Aplicable a Cualquier Módulo)

#### Paso 1: Auditar Módulo para Código Duplicado

**Aplicable a:** Cualquier módulo del sistema

1. Buscar archivo `permissions.py` en el módulo
2. Identificar clases de permisos con lógica similar
3. Identificar patrones comunes:
   - Verificación de autenticación
   - Verificación de admin/staff
   - Verificación de permisos específicos
   - Validación de empresa

**Herramientas:**
- Buscar patrones con grep: `class.*Permission|has_permission|has_object_permission`
- Revisar código duplicado manualmente

#### Paso 2: Usar Clases Base Genéricas Existentes

**Aplicable a:** Todos los módulos (después de Fase 1)

1. Importar clases base desde `core.permissions.base`
2. Identificar qué clase base genérica usar:
   - `BaseEmpresaPermission` - Para permisos con validación de empresa
   - `BaseModelPermission` - Para permisos de modelos específicos
   - `BaseActionPermission` - Para permisos de acciones personalizadas

#### Paso 3: Refactorizar Clases del Módulo

**Aplicable a:** Cualquier módulo

1. Hacer que clases existentes hereden de clase base genérica
2. Pasar parámetros de configuración al constructor:
   - `permission_codename` - Código del permiso Django
   - `message` - Mensaje de error personalizado
3. Eliminar código duplicado (mantener solo lógica específica del módulo)

**Ejemplo genérico:**
```python
# ANTES (código duplicado en cualquier módulo)
class CanActionModel(permissions.BasePermission):
    def has_permission(self, request, view):
        if not request.user.is_authenticated:
            return False
        if request.user.is_superuser or request.user.is_staff:
            return True
        return request.user.has_perm('app.action_model')
    # ... más código duplicado

# DESPUÉS (usando clase base genérica)
from core.permissions.base import BaseEmpresaPermission

class CanActionModel(BaseEmpresaPermission):
    def __init__(self):
        super().__init__(
            permission_codename='app.action_model',
            message='No tiene permiso para realizar esta acción.'
        )
```

#### Paso 4: Actualizar Tests del Módulo

**Aplicable a:** Todos los módulos

1. Verificar que tests existentes sigan funcionando (compatibilidad)
2. Los tests de la clase base genérica ya cubren la lógica común
3. Simplificar tests del módulo (solo probar lógica específica)

#### Paso 5: Documentar Cambios del Módulo

**Aplicable a:** Todos los módulos

1. Documentar qué clase base genérica se usa
2. Documentar cualquier extensión específica del módulo
3. Actualizar ejemplos de uso del módulo

---

## Especificación Técnica

### Clase Base Genérica: `BaseEmpresaPermission`

**Ubicación:** `backend/core/permissions/base.py`

**Propósito:** Clase base **genérica y reutilizable** para permisos que requieren validación de empresa y permisos específicos. **Aplicable a cualquier módulo del sistema.**

**Compatibilidad:** Django 6.0 - Usa el sistema de permisos nativo de Django 6.0

**Parámetros del Constructor (Genéricos):**
- `permission_codename` (str): Código del permiso requerido según formato Django 6.0 (ej: 'activos.depreciar_activofijo', 'compras.aprobar_compra', 'ventas.anular_venta')
- `message` (str): Mensaje de error personalizado (opcional)

**Nota:** Usa el sistema de permisos nativo de Django 6.0 (`user.has_perm()`)

**Métodos Públicos (Genéricos):**
- `has_permission(request, view)` - Verifica permiso a nivel de vista (genérico)
- `has_object_permission(request, view, obj)` - Verifica permiso a nivel de objeto (genérico)

**Métodos Protegidos (Extensibles):**
- `_is_admin_or_staff(user)` - Verifica si es admin/staff (genérico)
- `_has_permission_codename(user)` - Verifica permiso específico (genérico)
- `_belongs_to_same_empresa(obj, user)` - Valida empresa (genérico, funciona con cualquier modelo que tenga campo 'empresa')

**Comportamiento (Genérico):**
1. Superusuarios y staff siempre tienen acceso (aplicable a todos los módulos)
2. Usuarios normales requieren permiso específico (configurable por módulo)
3. A nivel de objeto, valida que pertenezca a la misma empresa (genérico para cualquier modelo)

**Uso en cualquier módulo:**
```python
# activos/permissions.py
class CanDepreciarActivo(BaseEmpresaPermission):
    def __init__(self):
        super().__init__('activos.depreciar_activofijo', 'Mensaje...')

# compras/permissions.py  
class CanAprobarCompra(BaseEmpresaPermission):
    def __init__(self):
        super().__init__('compras.aprobar_compra', 'Mensaje...')

# ventas/permissions.py
class CanAnularVenta(BaseEmpresaPermission):
    def __init__(self):
        super().__init__('ventas.anular_venta', 'Mensaje...')
```

### Mixin: `EmpresaValidationMixin`

**Ubicación:** `backend/core/permissions/mixins.py`

**Propósito:** Proporciona validación de empresa como mixin.

**Métodos:**
- `_belongs_to_same_empresa(obj, user)` - Valida empresa
- `_validate_empresa(obj, user)` - Validación completa con mensajes de error

### Mixin: `AdminStaffMixin`

**Ubicación:** `backend/core/permissions/mixins.py`

**Propósito:** Proporciona verificación de admin/staff como mixin.

**Métodos:**
- `_is_admin_or_staff(user)` - Verifica admin/staff
- `_check_admin_staff(user)` - Con logging opcional

### Utilidades: `utils.py`

**Ubicación:** `backend/core/permissions/utils.py`

**Propósito:** Proporciona funciones auxiliares genéricas, decoradores reutilizables y helpers para testing que facilitan el trabajo con permisos en todo el sistema.

**Compatibilidad:** Django 6.0 - Usa el sistema de permisos nativo de Django 6.0

---

#### 1. Helpers para Verificación de Permisos

##### `check_permission(user, permission_codename) -> bool`

Verifica si un usuario tiene un permiso específico, considerando superusuarios y staff.

**Parámetros:**
- `user` (User): Instancia del usuario de Django
- `permission_codename` (str): Código del permiso Django (ej: 'activos.depreciar_activofijo')

**Returns:**
- `bool`: True si el usuario tiene el permiso, es superusuario o staff

**Comportamiento:**
- Superusuarios y staff siempre retornan True
- Usuarios normales requieren el permiso específico

**Ejemplo de uso:**
```python
from core.permissions.utils import check_permission

if check_permission(request.user, 'activos.depreciar_activofijo'):
    # Usuario puede depreciar activos
    pass
```

##### `check_empresa_permission(user, obj, permission_codename) -> bool`

Verifica permiso específico y que el objeto pertenezca a la misma empresa del usuario.

**Parámetros:**
- `user` (User): Instancia del usuario de Django
- `obj` (Model): Instancia del modelo con campo 'empresa'
- `permission_codename` (str): Código del permiso Django

**Returns:**
- `bool`: True si tiene permiso Y pertenece a la misma empresa

**Comportamiento:**
- Superusuarios y staff siempre retornan True
- Valida permiso específico
- Valida que `obj.empresa == user.empresa`

**Ejemplo de uso:**
```python
from core.permissions.utils import check_empresa_permission

activo = ActivoFijo.objects.get(pk=1)
if check_empresa_permission(request.user, activo, 'activos.change_activofijo'):
    # Usuario puede editar este activo de su empresa
    pass
```

##### `user_has_any_permission(user, permissions) -> bool`

Verifica si el usuario tiene al menos uno de los permisos especificados.

**Parámetros:**
- `user` (User): Instancia del usuario de Django
- `permissions` (list[str]): Lista de códigos de permisos

**Returns:**
- `bool`: True si tiene al menos uno de los permisos

**Ejemplo de uso:**
```python
from core.permissions.utils import user_has_any_permission

perms = ['activos.depreciar_activofijo', 'activos.cambiar_estado_activofijo']
if user_has_any_permission(request.user, perms):
    # Usuario tiene al menos uno de los permisos
    pass
```

##### `user_has_all_permissions(user, permissions) -> bool`

Verifica si el usuario tiene todos los permisos especificados.

**Parámetros:**
- `user` (User): Instancia del usuario de Django
- `permissions` (list[str]): Lista de códigos de permisos

**Returns:**
- `bool`: True si tiene todos los permisos

**Ejemplo de uso:**
```python
from core.permissions.utils import user_has_all_permissions

perms = ['activos.depreciar_activofijo', 'activos.cambiar_estado_activofijo']
if user_has_all_permissions(request.user, perms):
    # Usuario tiene todos los permisos requeridos
    pass
```

##### `belongs_to_same_empresa(obj, user) -> bool`

Verifica si un objeto pertenece a la misma empresa que el usuario.

**Parámetros:**
- `obj` (Model): Instancia del modelo con campo 'empresa'
- `user` (User): Instancia del usuario con campo 'empresa'

**Returns:**
- `bool`: True si pertenecen a la misma empresa

**Ejemplo de uso:**
```python
from core.permissions.utils import belongs_to_same_empresa

if belongs_to_same_empresa(activo, request.user):
    # El activo pertenece a la empresa del usuario
    pass
```

---

#### 2. Decoradores Reutilizables

##### `require_permission(permission_codename)`

Decorador para asignar un permiso específico a una acción personalizada de ViewSet.

**Parámetros:**
- `permission_codename` (str): Código del permiso Django requerido

**Uso:**
```python
from rest_framework.decorators import action
from core.permissions.utils import require_permission

class ActivoFijoViewSet(viewsets.ModelViewSet):
    @action(detail=True, methods=['post'])
    @require_permission('activos.depreciar_activofijo')
    def depreciar(self, request, pk=None):
        # Esta acción requiere el permiso 'activos.depreciar_activofijo'
        pass
```

**Comportamiento:**
- Asigna el atributo `permission_required` a la función
- Compatible con `ActionBasedPermission` y otras clases de permisos que verifican este atributo

##### `require_same_empresa`

Decorador que verifica que el objeto pertenezca a la empresa del usuario antes de ejecutar la acción.

**Uso:**
```python
from rest_framework.decorators import action
from core.permissions.utils import require_same_empresa

class ActivoFijoViewSet(viewsets.ModelViewSet):
    @action(detail=True, methods=['post'])
    @require_same_empresa
    def operacion_especial(self, request, pk=None):
        # Verifica automáticamente que el activo pertenezca a la empresa del usuario
        activo = self.get_object()
        # ... lógica de la acción
        pass
```

**Comportamiento:**
- Verifica `obj.empresa == user.empresa` antes de ejecutar
- Retorna 403 si no pertenece a la misma empresa

---

#### 3. Funciones de Utilidad para Testing

##### `create_user_with_permission(permission_codename, empresa=None, **kwargs) -> User`

Crea un usuario de prueba con un permiso específico asignado.

**Parámetros:**
- `permission_codename` (str): Código del permiso a asignar
- `empresa` (Empresa, optional): Empresa a asignar al usuario
- `**kwargs`: Argumentos adicionales para `User.objects.create_user()`

**Returns:**
- `User`: Usuario creado con el permiso asignado

**Ejemplo de uso:**
```python
from core.permissions.utils import create_user_with_permission

def test_depreciar_activo(self):
    user = create_user_with_permission(
        'activos.depreciar_activofijo',
        empresa=self.empresa,
        username='testuser'
    )
    # Usuario tiene el permiso asignado
    self.assertTrue(user.has_perm('activos.depreciar_activofijo'))
```

##### `create_mock_request(user, method='GET', data=None) -> Request`

Crea un objeto request mock para tests de permisos.

**Parámetros:**
- `user` (User): Usuario a asignar al request
- `method` (str): Método HTTP ('GET', 'POST', 'PUT', 'DELETE')
- `data` (dict, optional): Datos del request body

**Returns:**
- `Request`: Objeto request mock con el usuario asignado

**Ejemplo de uso:**
```python
from core.permissions.utils import create_mock_request

def test_permission(self):
    user = self.create_user()
    request = create_mock_request(user, method='POST', data={'estado': 'ACTIVO'})
    permission = CanDepreciarActivo()
    self.assertTrue(permission.has_permission(request, None))
```

##### `assert_has_permission(permission_class, user, obj=None, should_have=True, msg=None)`

Helper de assert para verificar permisos en tests.

**Parámetros:**
- `permission_class`: Clase de permiso a probar
- `user` (User): Usuario a verificar
- `obj` (Model, optional): Objeto para `has_object_permission`
- `should_have` (bool): Si se espera que tenga permiso (True) o no (False)
- `msg` (str, optional): Mensaje personalizado para el assert

**Ejemplo de uso:**
```python
from core.permissions.utils import assert_has_permission

def test_permission(self):
    user = self.create_user_with_permission('activos.depreciar_activofijo')
    activo = self.create_activo()
    
    assert_has_permission(
        CanDepreciarActivo(),
        user,
        obj=activo,
        should_have=True
    )
```

##### `create_test_empresa(name='Test Empresa') -> Empresa`

Crea una empresa de prueba para tests.

**Parámetros:**
- `name` (str): Nombre de la empresa

**Returns:**
- `Empresa`: Empresa creada

**Ejemplo de uso:**
```python
from core.permissions.utils import create_test_empresa

def setUp(self):
    self.empresa = create_test_empresa('Mi Empresa Test')
    self.user.empresa = self.empresa
    self.user.save()
```

---

#### 4. Utilidades Avanzadas (Opcional - Fase 4)

##### `get_cached_permission(user, permission_codename, cache_timeout=300) -> bool`

Obtiene resultado de verificación de permiso desde caché si está disponible.

**Parámetros:**
- `user` (User): Instancia del usuario
- `permission_codename` (str): Código del permiso
- `cache_timeout` (int): Tiempo de expiración del caché en segundos (default: 300)

**Returns:**
- `bool`: Resultado de la verificación de permiso

**Nota:** Requiere configuración de caché en Django settings.

##### `log_permission_check(user, permission, granted, obj=None, request=None)`

Registra verificaciones de permisos para auditoría.

**Parámetros:**
- `user` (User): Usuario que verificó el permiso
- `permission` (str): Código del permiso verificado
- `granted` (bool): Si el permiso fue otorgado o denegado
- `obj` (Model, optional): Objeto relacionado
- `request` (Request, optional): Request HTTP para obtener IP, etc.

**Comportamiento:**
- Registra en logs del sistema
- Puede integrarse con sistema de auditoría externo

**Ejemplo de uso:**
```python
from core.permissions.utils import log_permission_check

def has_permission(self, request, view):
    granted = check_permission(request.user, 'activos.depreciar_activofijo')
    log_permission_check(
        request.user,
        'activos.depreciar_activofijo',
        granted,
        request=request
    )
    return granted
```

---

#### Estructura del Archivo `utils.py`

```python
"""
Utilidades genéricas para permisos - Infraestructura Global

Este módulo proporciona funciones auxiliares, decoradores y helpers
para facilitar el trabajo con permisos en todo el sistema.
"""
import logging
from functools import wraps
from django.core.cache import cache
from rest_framework.exceptions import PermissionDenied

logger = logging.getLogger(__name__)

# Helpers para verificación de permisos
def check_permission(user, permission_codename):
    """..."""
    pass

def check_empresa_permission(user, obj, permission_codename):
    """..."""
    pass

# ... más helpers ...

# Decoradores
def require_permission(permission_codename):
    """..."""
    pass

# ... más decoradores ...

# Helpers para testing
def create_user_with_permission(permission_codename, empresa=None, **kwargs):
    """..."""
    pass

# ... más helpers de testing ...

# Utilidades avanzadas (opcional)
def get_cached_permission(user, permission_codename, cache_timeout=300):
    """..."""
    pass

def log_permission_check(user, permission, granted, obj=None, request=None):
    """..."""
    pass
```

---

#### Exportaciones en `__init__.py`

Las funciones de `utils.py` deben exportarse en `core/permissions/__init__.py`:

```python
# Utilidades
from .utils import (
    check_permission,
    check_empresa_permission,
    user_has_any_permission,
    user_has_all_permissions,
    belongs_to_same_empresa,
    require_permission,
    require_same_empresa,
    create_user_with_permission,
    create_mock_request,
    assert_has_permission,
    create_test_empresa,
)

__all__ = [
    # ... clases base y mixins ...
    # Utilidades
    'check_permission',
    'check_empresa_permission',
    'user_has_any_permission',
    'user_has_all_permissions',
    'belongs_to_same_empresa',
    'require_permission',
    'require_same_empresa',
    'create_user_with_permission',
    'create_mock_request',
    'assert_has_permission',
    'create_test_empresa',
]
```

---

## Plan de Implementación

### Fase 1: Infraestructura Base (Sprint 1)

**Duración estimada:** 2-3 días

**Tareas:**
1. ✅ Crear estructura de directorios `core/permissions/`
2. ✅ Implementar `BaseEmpresaPermission`
3. ✅ Implementar mixins básicos
4. ⚠️ Implementar `utils.py` con helpers y decoradores (Opcional - Fase 4)
5. ✅ Escribir documentación básica
6. ✅ Crear tests unitarios para clase base

**Criterios de aceptación:**
- Clase base funciona correctamente
- Tests pasan al 100%
- Documentación completa
- `utils.py` implementado (opcional, puede ser Fase 4)

### Fase 2: Refactorizar Módulos Existentes (Sprint 1-2)

**Duración estimada:** 3-5 días (dependiendo de cantidad de módulos)

**Estrategia:** Refactorizar módulo por módulo usando las clases base genéricas.

**Módulos prioritarios:**

1. **`activos/permissions.py`** (1-2 días)
   - Refactorizar `CanDepreciarActivo` → `BaseEmpresaPermission`
   - Refactorizar `CanCambiarEstadoActivo` → `BaseEmpresaPermission`
   - Refactorizar `CanVerProyeccion` → `BaseEmpresaPermission`
   - Verificar tests

2. **`usuarios/permissions.py`** (1 día)
   - Refactorizar `IsAdminOrSameEmpresa` → `BaseEmpresaPermission`
   - Revisar otros permisos personalizados
   - Verificar tests

3. **Otros módulos** (1-2 días según auditoría)
   - Auditar: `compras/`, `ventas/`, `inventario/`, `productos/`, etc.
   - Refactorizar permisos personalizados encontrados
   - Verificar tests

**Criterios de aceptación (por módulo):**
- Todos los tests del módulo pasan
- Código reducido en ~60%
- Funcionalidad idéntica
- Uso de clases base genéricas de `core/permissions/`

### Fase 3: Refactorizar Otros Módulos (Sprint 2)

**Duración estimada:** 2-3 días

**Tareas:**
1. ✅ Auditar otros módulos para permisos personalizados
2. ✅ Refactorizar `IsAdminOrSameEmpresa` en usuarios
3. ✅ Identificar y refactorizar otros permisos según necesidad
4. ✅ Actualizar tests

**Criterios de aceptación:**
- Código duplicado eliminado
- Tests pasan
- Documentación actualizada

### Fase 4: Utilidades y Mejoras (Sprint 2)

**Duración estimada:** 1-2 días

**Tareas:**
1. ⚠️ Implementar `utils.py` con todas las utilidades especificadas
   - Helpers para verificación de permisos
   - Decoradores reutilizables (`require_permission`, `require_same_empresa`)
   - Funciones de utilidad para testing
   - Utilidades avanzadas (caché, logging) - Opcional
2. ⚠️ Crear tests para utilidades de `utils.py`
3. ✅ Documentar mejores prácticas
4. ✅ Crear guía de migración completa

**Criterios de aceptación:**
- `utils.py` implementado según especificación técnica
- Todas las funciones tienen tests
- Utilidades funcionan correctamente
- Documentación completa con ejemplos
- Exportaciones correctas en `__init__.py`

---

## Ejemplo de Implementación

### Código Antes (Duplicado en Múltiples Módulos)

**Ejemplo en activos/permissions.py:**
```python
class CanDepreciarActivo(permissions.BasePermission):
    message = 'No tiene permiso para registrar depreciaciones de activos.'
    def has_permission(self, request, view):
        if not request.user.is_authenticated: return False
        if request.user.is_superuser or request.user.is_staff: return True
        return request.user.has_perm('activos.depreciar_activofijo')
    def has_object_permission(self, request, view, obj):
        if not request.user.is_authenticated: return False
        if request.user.is_superuser or request.user.is_staff: return True
        if not request.user.has_perm('activos.depreciar_activofijo'): return False
        if hasattr(obj, 'empresa') and hasattr(request.user, 'empresa'):
            return obj.empresa == request.user.empresa
        return False
```

**Mismo patrón repetido en otros módulos:**
- `compras/permissions.py` - `CanAprobarCompra` (mismo código, diferente permiso)
- `ventas/permissions.py` - `CanAnularVenta` (mismo código, diferente permiso)
- `usuarios/permissions.py` - `IsAdminOrSameEmpresa` (mismo código, diferente permiso)
- Y así en cada módulo...

**Líneas de código:** ~50 líneas por módulo × N módulos = Cientos de líneas duplicadas

### Código Después (Solución Genérica Global)

**Infraestructura global (una sola vez):**
```python
# core/permissions/base.py - GENÉRICO PARA TODO EL SISTEMA
class BaseEmpresaPermission(permissions.BasePermission):
    """Clase base genérica aplicable a cualquier módulo"""
    def __init__(self, permission_codename=None, message=None):
        self.permission_codename = permission_codename
        self.message = message or 'No tiene permiso para realizar esta operación.'
    
    def _is_admin_or_staff(self, user):
        return user.is_superuser or user.is_staff
    
    def _has_permission_codename(self, user):
        if not self.permission_codename:
            return False
        return user.has_perm(self.permission_codename)
    
    def _belongs_to_same_empresa(self, obj, user):
        if not (hasattr(obj, 'empresa') and hasattr(user, 'empresa')):
            return False
        return obj.empresa == user.empresa
    
    def has_permission(self, request, view):
        if not request.user.is_authenticated:
            return False
        if self._is_admin_or_staff(request.user):
            return True
        return self._has_permission_codename(request.user)
    
    def has_object_permission(self, request, view, obj):
        if not request.user.is_authenticated:
            return False
        if self._is_admin_or_staff(request.user):
            return True
        if not self._has_permission_codename(request.user):
            return False
        return self._belongs_to_same_empresa(obj, request.user)
```

**Uso en cualquier módulo (solo configuración):**
```python
# activos/permissions.py
from core.permissions.base import BaseEmpresaPermission

class CanDepreciarActivo(BaseEmpresaPermission):
    def __init__(self):
        super().__init__('activos.depreciar_activofijo', 'Mensaje...')

# compras/permissions.py - MISMO PATRÓN
from core.permissions.base import BaseEmpresaPermission

class CanAprobarCompra(BaseEmpresaPermission):
    def __init__(self):
        super().__init__('compras.aprobar_compra', 'Mensaje...')

# ventas/permissions.py - MISMO PATRÓN
from core.permissions.base import BaseEmpresaPermission

class CanAnularVenta(BaseEmpresaPermission):
    def __init__(self):
        super().__init__('ventas.anular_venta', 'Mensaje...')
```

**Líneas de código:** 
- Infraestructura global: ~40 líneas (una sola vez)
- Por módulo: ~5 líneas (solo configuración)
- **Reducción:** 60-70% menos código por módulo
- **Reducción total:** 500+ líneas eliminadas en todo el sistema

---

## Consideraciones de Seguridad

### Validaciones Críticas

1. **Autenticación:** Siempre verificar `is_authenticated` primero
2. **Admin/Staff:** Verificar antes de permisos específicos (más rápido)
3. **Permisos Específicos:** Verificar después de admin/staff
4. **Empresa:** Validar en `has_object_permission` para evitar acceso cruzado

### Mejores Prácticas

1. **Nunca omitir validación de empresa** en permisos de objetos
2. **Siempre verificar autenticación** antes de cualquier otra validación
3. **Usar mensajes de error claros** para debugging
4. **Logging opcional** para auditoría de accesos denegados

---

## Testing

### Tests Requeridos para Clase Base

1. **Tests de `has_permission`:**
   - Usuario no autenticado → False
   - Superusuario → True
   - Staff → True
   - Usuario con permiso → True
   - Usuario sin permiso → False

2. **Tests de `has_object_permission`:**
   - Usuario no autenticado → False
   - Superusuario → True
   - Staff → True
   - Usuario con permiso + misma empresa → True
   - Usuario con permiso + diferente empresa → False
   - Usuario sin permiso → False

3. **Tests de Integración:**
   - Verificar que permisos derivados funcionan correctamente
   - Verificar compatibilidad con código existente

### Estrategia de Testing

1. **Tests unitarios** para clase base
2. **Tests de integración** para permisos derivados
3. **Tests de regresión** para verificar que funcionalidad existente no se rompe

---

## Métricas de Éxito

### Métricas Cuantitativas

1. **Reducción de código:**
   - Objetivo: 60-70% menos código duplicado
   - Métrica: Líneas de código antes vs después

2. **Cobertura de tests:**
   - Objetivo: Mantener o mejorar cobertura actual
   - Métrica: % de cobertura de código

3. **Tiempo de desarrollo:**
   - Objetivo: Reducir tiempo para crear nuevos permisos
   - Métrica: Tiempo promedio para crear permiso nuevo

### Métricas Cualitativas

1. **Mantenibilidad:**
   - Facilidad para modificar lógica común
   - Consistencia entre permisos

2. **Legibilidad:**
   - Claridad del código
   - Facilidad de comprensión

3. **Extensibilidad:**
   - Facilidad para agregar nuevos permisos
   - Facilidad para agregar nuevas validaciones

---

## Riesgos y Mitigaciones

### Riesgo 1: Romper Funcionalidad Existente

**Probabilidad:** Media  
**Impacto:** Alto

**Mitigación:**
- Tests exhaustivos antes de refactorizar
- Refactorización gradual módulo por módulo
- Revisión de código cuidadosa
- Pruebas en ambiente de desarrollo primero

### Riesgo 2: Sobre-ingeniería

**Probabilidad:** Baja  
**Impacto:** Medio

**Mitigación:**
- Mantener simplicidad
- No crear abstracciones innecesarias
- Validar necesidad antes de crear nuevas clases base

### Riesgo 3: Dificultad de Migración

**Probabilidad:** Baja  
**Impacto:** Medio

**Mitigación:**
- Documentación clara de migración
- Ejemplos paso a paso
- Soporte durante migración

---

## Checklist de Implementación

### Fase 1: Infraestructura Base ✅
- [x] Crear directorio `core/permissions/`
- [x] Crear `__init__.py` con exports
- [x] Implementar `BaseEmpresaPermission`
- [x] Implementar mixins básicos
- [x] Escribir docstrings completos
- [x] Crear tests unitarios (29 tests)
- [x] Documentar uso y ejemplos

### Fase 2: Refactorizar Módulos Existentes ✅
- [x] Auditar todos los módulos para permisos personalizados
- [x] Refactorizar `activos/permissions.py` (reducción 46%)
  - [x] Refactorizar `CanDepreciarActivo`
  - [x] Refactorizar `CanCambiarEstadoActivo`
  - [x] Refactorizar `CanVerProyeccion`
- [x] Refactorizar `usuarios/permissions.py`
  - [x] Refactorizar `IsAdminOrSameEmpresa`
  - [x] Refactorizar `IsOwnerOrReadOnly`
  - [x] Refactorizar `IsAdminUserOrReadOnly`
- [x] Refactorizar otros módulos identificados (`core/views.py`)
- [x] Verificar tests existentes pasan en todos los módulos
- [x] Medir reducción de código global (~46% en activos)
- [x] Actualizar documentación de módulos refactorizados

### Fase 3: Refactorizar Otros Módulos ✅
- [x] Auditar módulos para permisos personalizados
- [x] Refactorizar `IsAdminOrSameEmpresa`
- [x] Refactorizar otros permisos identificados (`IsAdminRole` en core/views.py)
- [x] Verificar tests (63 tests de permisos pasan)
- [x] Documentar cambios

### Fase 4: Utilidades y Mejoras ✅
- [x] Implementar `utils.py` completo (~350 líneas)
  - [x] Helpers para verificación de permisos (`check_permission`, `check_empresa_permission`, etc.)
  - [x] Decoradores reutilizables (`require_permission`, `require_same_empresa`)
  - [x] Funciones de utilidad para testing (`create_user_with_permission`, `create_mock_request`, etc.)
  - [x] Utilidades avanzadas (caché, logging, `get_user_permissions_summary`)
- [x] Crear tests para todas las funciones de `utils.py` (34 tests nuevos)
- [x] Exportar funciones en `__init__.py`
- [x] Documentar mejores prácticas
- [x] Crear guía de migración completa
- [x] Actualizar documentación general

**Estado Final:** ✅ Todas las fases completadas
**Total Tests de Permisos:** 63
**Commits Relacionados:**
- `feat: Implement global permissions infrastructure (core/permissions)`
- `refactor: Update usuarios/permissions.py to use core mixins`
- `feat: Add permissions utilities module (Phase 4)`

---

## Referencias y Recursos

### Documentación Técnica

**Django 6.0:**
- [Permissions System](https://docs.djangoproject.com/en/6.0/topics/auth/default/#permissions-and-authorization)
- [Custom Permissions](https://docs.djangoproject.com/en/6.0/topics/auth/customizing/#custom-permissions)
- [Permission Checks](https://docs.djangoproject.com/en/6.0/topics/auth/default/#permission-checking)

**Django REST Framework:**
- [Permissions](https://www.django-rest-framework.org/api-guide/permissions/)
- [Custom Permissions](https://www.django-rest-framework.org/api-guide/permissions/#custom-permissions)

### Patrones de Diseño
- Strategy Pattern (para diferentes tipos de validación)
- Template Method Pattern (para estructura común)
- Mixin Pattern (para composición)

### Código de Referencia
- `backend/usuarios/permissions.py` - `ActionBasedPermission` (ejemplo de permiso genérico existente)
- `backend/activos/permissions.py` - Permisos actuales (caso de uso para refactorización)
- `backend/core/mixins.py` - Ejemplos de mixins genéricos existentes (patrón similar)

### Módulos que se Beneficiarán
- ✅ `activos/` - Identificado con código duplicado
- ✅ `usuarios/` - Tiene `IsAdminOrSameEmpresa` con lógica similar
- ✅ `compras/` - Posibles permisos personalizados
- ✅ `ventas/` - Posibles permisos personalizados
- ✅ `inventario/` - Posibles permisos personalizados
- ✅ `productos/` - Posibles permisos personalizados
- ✅ Cualquier módulo futuro que necesite permisos personalizados

---

## Notas Adicionales

### Compatibilidad

- ✅ **Django 6.0** - Compatible con todas las características de Django 6.0
- ✅ **Django REST Framework** - Compatible con DRF estándar
- ✅ **Sistema de Permisos de Django 6.0** - Usa el sistema nativo de permisos
- ✅ No requiere cambios en modelos
- ✅ No requiere cambios en serializers
- ✅ Aprovecha características de Django 6.0 (mejoras en permisos, validaciones, etc.)

### Características de Django 6.0 Aprovechadas

**Sistema de Permisos de Django 6.0:**
- ✅ Usa `user.has_perm()` nativo de Django 6.0
- ✅ Compatible con permisos personalizados definidos en `Meta.permissions`
- ✅ Aprovecha mejoras de rendimiento en verificación de permisos
- ✅ Compatible con grupos y permisos de Django 6.0

**Características Adicionales Disponibles:**
- Mejoras en `ContentType` para permisos más eficientes
- Mejor integración con el sistema de autenticación
- Soporte mejorado para permisos a nivel de objeto

### Extensibilidad Futura

La arquitectura propuesta permite fácilmente:
- Agregar validaciones adicionales (IP, ubicación, horario)
- Crear nuevos tipos de permisos base
- Integrar con sistemas externos de permisos
- Agregar logging y auditoría
- Aprovechar nuevas características de Django 6.0 cuando estén disponibles

### Mantenimiento

- **Responsable:** Equipo de desarrollo backend
- **Revisión:** Cada 6 meses o cuando se agreguen nuevos módulos
- **Actualización:** Según necesidades del proyecto

---

**Última Actualización:** 2025-01-27  
**Versión:** 1.0  
**Autor:** QA Team / Arquitectura  
**Estado:** Pendiente de Aprobación

