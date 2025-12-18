# Módulo de Clientes

## Descripción General

El módulo de clientes gestiona la información de los clientes del sistema, incluyendo sus datos de contacto, identificación, límites de crédito y categorización. Este módulo es fundamental para el proceso de ventas y facturación.

## Estructura del Módulo

### Modelos

#### CategoriaCliente

Categorías que agrupan clientes con características similares y permiten aplicar descuentos generales.

**Campos:**
- `empresa` (ForeignKey): Empresa a la que pertenece la categoría (requerido)
- `nombre` (CharField, max_length=100): Nombre de la categoría
- `descripcion` (TextField): Descripción opcional
- `descuento_porcentaje` (DecimalField): Descuento general para clientes de esta categoría (0-100)
- `uuid` (UUIDField): Identificador único universal
- `activa` (BooleanField): Indica si la categoría está activa
- `fecha_creacion` (DateTimeField): Fecha de creación (auto)
- `fecha_actualizacion` (DateTimeField): Fecha de última actualización (auto)
- `usuario_creacion` (ForeignKey): Usuario que creó el registro
- `usuario_modificacion` (ForeignKey): Usuario que modificó el registro

**Restricciones:**
- `unique_together`: (`empresa`, `nombre`) - No puede haber dos categorías con el mismo nombre en la misma empresa

#### Cliente

Información completa de los clientes del sistema.

**Campos:**
- `empresa` (ForeignKey): Empresa a la que pertenece el cliente (requerido)
- `categoria` (ForeignKey): Categoría del cliente (opcional)
- `uuid` (UUIDField): Identificador único universal
- `nombre` (CharField, max_length=200): Nombre del cliente (requerido)
- `tipo_identificacion` (CharField): Tipo de identificación (RNC, CÉDULA, PASAPORTE, OTRO)
- `numero_identificacion` (CharField, max_length=50): Número de identificación
- `telefono` (CharField, max_length=20): Teléfono de contacto
- `correo_electronico` (EmailField): Correo electrónico
- `direccion` (TextField): Dirección física
- `limite_credito` (DecimalField): Límite de crédito del cliente (default: 0)
- `vendedor_asignado` (ForeignKey): Vendedor asignado por defecto (opcional)
- `activo` (BooleanField): Indica si el cliente está activo
- `fecha_creacion` (DateTimeField): Fecha de creación (auto)
- `fecha_actualizacion` (DateTimeField): Fecha de última actualización (auto)
- `usuario_creacion` (ForeignKey): Usuario que creó el registro
- `usuario_modificacion` (ForeignKey): Usuario que modificó el registro
- `idempotency_key` (CharField): Clave para operaciones idempotentes

**Restricciones:**
- `unique_together`: (`empresa`, `numero_identificacion`) - No puede haber dos clientes con el mismo número de identificación en la misma empresa
- Validación: Si `tipo_identificacion` es 'RNC', `numero_identificacion` es obligatorio

### Serializers

#### CategoriaClienteSerializer

Serializer para `CategoriaCliente` con todos los campos. Los campos de auditoría son de solo lectura.

#### ClienteSerializer

Serializer para `Cliente` con todos los campos. Incluye:
- `categoria_nombre`: Campo calculado que muestra el nombre de la categoría (read-only)
- Validación personalizada para RNC obligatorio

### Viewsets (API Endpoints)

#### CategoriaClienteViewSet

**Endpoint:** `/api/v1/categorias-clientes/`

**Características:**
- Hereda de `IdempotencyMixin` para operaciones idempotentes
- Filtrado automático por empresa del usuario autenticado
- Búsqueda por nombre
- Ordenamiento por nombre
- Requiere autenticación y permisos basados en acciones

**Métodos HTTP:**
- `GET /api/v1/categorias-clientes/` - Listar categorías
- `POST /api/v1/categorias-clientes/` - Crear categoría
- `GET /api/v1/categorias-clientes/{id}/` - Obtener categoría
- `PUT /api/v1/categorias-clientes/{id}/` - Actualizar categoría completa
- `PATCH /api/v1/categorias-clientes/{id}/` - Actualizar categoría parcial
- `DELETE /api/v1/categorias-clientes/{id}/` - Eliminar categoría

#### ClienteViewSet

**Endpoint:** `/api/v1/clientes/`

**Características:**
- Hereda de `IdempotencyMixin` para operaciones idempotentes
- Filtrado automático por empresa del usuario autenticado
- Búsqueda por nombre, número de identificación y teléfono
- Ordenamiento por nombre y fecha de creación
- Requiere autenticación y permisos basados en acciones

**Métodos HTTP:**
- `GET /api/v1/clientes/` - Listar clientes
- `POST /api/v1/clientes/` - Crear cliente
- `GET /api/v1/clientes/{id}/` - Obtener cliente
- `PUT /api/v1/clientes/{id}/` - Actualizar cliente completo
- `PATCH /api/v1/clientes/{id}/` - Actualizar cliente parcial
- `DELETE /api/v1/clientes/{id}/` - Eliminar cliente

**Acciones Personalizadas:**
- `GET /api/v1/clientes/{id}/historial_compras/` - Obtener historial de facturas del cliente
- `GET /api/v1/clientes/{id}/historial_pagos/` - Obtener historial de pagos del cliente

### Admin de Django

Ambos modelos están registrados en el admin de Django con configuraciones personalizadas:

#### CategoriaClienteAdmin
- Lista: nombre, descuento, estado activo, empresa, fecha de creación
- Filtros: activa, empresa, fecha de creación
- Búsqueda: nombre, descripción
- Campos de solo lectura: uuid, fechas, usuarios

#### ClienteAdmin
- Lista: nombre, tipo identificación, número identificación, teléfono, categoría, vendedor, estado activo, empresa
- Filtros: activo, tipo identificación, categoría, vendedor, empresa, fecha de creación
- Búsqueda: nombre, número identificación, teléfono, correo
- Campos de solo lectura: uuid, idempotency_key, fechas, usuarios

## Características Principales

### Multi-empresa
- Todos los registros están asociados a una empresa
- El filtrado automático asegura que los usuarios solo vean datos de su empresa
- Las restricciones de unicidad son por empresa

### Auditoría
- Registro automático de usuario y fecha de creación
- Registro automático de usuario y fecha de modificación
- Campos UUID para identificación única

### Idempotencia
- Soporte para operaciones idempotentes mediante `idempotency_key`
- Previene duplicación de registros en operaciones repetidas

### Integración con Ventas
- Los clientes están vinculados a facturas y pagos
- Acciones personalizadas para consultar historial de compras y pagos
- Asignación de vendedor por defecto

## Ejemplos de Uso

### Crear una Categoría de Cliente

```http
POST /api/v1/categorias-clientes/
Content-Type: application/json
Authorization: Bearer {token}

{
  "nombre": "Mayorista",
  "descripcion": "Clientes mayoristas con descuentos especiales",
  "descuento_porcentaje": 15.00,
  "activa": true
}
```

### Crear un Cliente

```http
POST /api/v1/clientes/
Content-Type: application/json
Authorization: Bearer {token}

{
  "nombre": "Empresa ABC SRL",
  "tipo_identificacion": "RNC",
  "numero_identificacion": "123456789",
  "telefono": "809-555-1234",
  "correo_electronico": "contacto@empresaabc.com",
  "direccion": "Calle Principal #123, Santo Domingo",
  "limite_credito": 50000.00,
  "categoria": 1,
  "vendedor_asignado": 1,
  "activo": true
}
```

### Obtener Historial de Compras de un Cliente

```http
GET /api/v1/clientes/1/historial_compras/
Authorization: Bearer {token}
```

### Buscar Clientes

```http
GET /api/v1/clientes/?search=ABC
Authorization: Bearer {token}
```

## Notas de Implementación

### Cambios Recientes

1. **Campo `empresa` agregado**: Ambos modelos ahora incluyen el campo `empresa` como ForeignKey requerido
2. **Restricciones `unique_together` actualizadas**: Ahora incluyen `empresa` para permitir nombres/números duplicados entre diferentes empresas
3. **CategoriaClienteViewSet registrado**: El ViewSet ahora está disponible en `/api/v1/categorias-clientes/`
4. **IdempotencyMixin agregado**: `CategoriaClienteViewSet` ahora soporta operaciones idempotentes
5. **Admin configurado**: Ambos modelos están registrados en el admin de Django con configuraciones personalizadas

### Dependencias

- `empresas.Empresa`: Modelo de empresa (requerido)
- `vendedores.Vendedor`: Modelo de vendedor (opcional)
- `ventas.Factura`: Para historial de compras
- `ventas.PagoCaja`: Para historial de pagos

### Permisos

El módulo utiliza `ActionBasedPermission` que requiere:
- Autenticación del usuario
- Permisos específicos según la acción (crear, leer, actualizar, eliminar)

## Próximas Mejoras Sugeridas

1. Agregar validación de límite de crédito antes de crear facturas
2. Implementar historial de cambios (auditoría completa)
3. Agregar campos adicionales para segmentación de clientes
4. Implementar reportes de clientes por categoría
5. Agregar validación de correo electrónico único por empresa

