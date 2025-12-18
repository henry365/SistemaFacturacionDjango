# Módulo de Proveedores

## Descripción General

El módulo de proveedores gestiona la información de los proveedores del sistema, incluyendo sus datos de contacto, identificación, tipo de contribuyente y configuración para retenciones DGII. Este módulo es fundamental para el proceso de compras y gestión de cuentas por pagar.

## Estructura del Módulo

### Modelos

#### Proveedor

Información completa de los proveedores del sistema.

**Campos:**
- `empresa` (ForeignKey): Empresa a la que pertenece el proveedor (requerido)
- `uuid` (UUIDField): Identificador único universal
- `nombre` (CharField, max_length=200): Nombre del proveedor (requerido)
- `tipo_identificacion` (CharField): Tipo de identificación (RNC, CÉDULA, PASAPORTE, OTRO)
- `numero_identificacion` (CharField, max_length=50): Número de identificación
- `tipo_contribuyente` (CharField): Tipo de contribuyente según DGII:
  - JURIDICA: Persona Jurídica
  - FISICA: Persona Física
  - INFORMAL: Proveedor Informal
  - ESTATAL: Gobierno / Estatal
  - EXTRANJERO: Extranjero
- `telefono` (CharField, max_length=20): Teléfono de contacto
- `correo_electronico` (EmailField): Correo electrónico
- `direccion` (TextField): Dirección física
- `es_internacional` (BooleanField): Indica si el proveedor es internacional
- `activo` (BooleanField): Indica si el proveedor está activo
- `fecha_creacion` (DateTimeField): Fecha de creación (auto)
- `fecha_actualizacion` (DateTimeField): Fecha de última actualización (auto)
- `usuario_creacion` (ForeignKey): Usuario que creó el registro
- `usuario_modificacion` (ForeignKey): Usuario que modificó el registro
- `idempotency_key` (CharField): Clave para operaciones idempotentes

**Restricciones:**
- `unique_together`: (`empresa`, `numero_identificacion`) - No puede haber dos proveedores con el mismo número de identificación en la misma empresa
- Validación: Si `tipo_identificacion` es 'RNC', `numero_identificacion` es obligatorio

### Serializers

#### ProveedorSerializer

Serializer para `Proveedor` con todos los campos. Incluye:
- `empresa_nombre`: Campo calculado que muestra el nombre de la empresa (read-only)
- Validaciones personalizadas:
  - Correo electrónico válido
  - Teléfono con formato válido (10-15 dígitos)
  - RNC obligatorio cuando tipo_identificacion es RNC
  - Número de identificación único por empresa

### Viewsets (API Endpoints)

#### ProveedorViewSet

**Endpoint:** `/api/v1/proveedores/`

**Características:**
- Hereda de `IdempotencyMixin` para operaciones idempotentes
- Filtrado automático por empresa del usuario autenticado
- Búsqueda por nombre, número de identificación, teléfono y correo electrónico
- Ordenamiento por nombre, fecha de creación y tipo de contribuyente
- Requiere autenticación y permisos basados en acciones

**Métodos HTTP:**
- `GET /api/v1/proveedores/` - Listar proveedores
- `POST /api/v1/proveedores/` - Crear proveedor
- `GET /api/v1/proveedores/{id}/` - Obtener proveedor
- `PUT /api/v1/proveedores/{id}/` - Actualizar proveedor completo
- `PATCH /api/v1/proveedores/{id}/` - Actualizar proveedor parcial
- `DELETE /api/v1/proveedores/{id}/` - Eliminar proveedor

**Filtros Específicos:**
- `?activo=true/false` - Filtrar por estado activo
- `?tipo_identificacion=RNC` - Filtrar por tipo de identificación
- `?tipo_contribuyente=JURIDICA` - Filtrar por tipo de contribuyente
- `?es_internacional=true/false` - Filtrar proveedores internacionales

**Acciones Personalizadas:**
- `GET /api/v1/proveedores/{id}/historial_compras/` - Obtener historial de compras del proveedor
- `GET /api/v1/proveedores/{id}/historial_ordenes/` - Obtener historial de órdenes de compra
- `GET /api/v1/proveedores/{id}/resumen/` - Obtener resumen con estadísticas del proveedor

### Admin de Django

El modelo está registrado en el admin de Django con configuraciones personalizadas:

#### ProveedorAdmin
- Lista: nombre, tipo identificación, número identificación, tipo contribuyente, teléfono, es internacional, estado activo, empresa, fecha de creación
- Filtros: activo, tipo identificación, tipo contribuyente, es internacional, empresa, fecha de creación
- Búsqueda: nombre, número identificación, teléfono, correo, dirección
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

### Integración con Compras
- Los proveedores están vinculados a compras y órdenes de compra
- Acciones personalizadas para consultar historial de compras y órdenes
- Estadísticas de compras y pagos pendientes

### Tipo de Contribuyente (DGII)
- Clasificación según reglas de retención de la DGII
- Determina las reglas de retención de ITBIS e ISR
- Soporte para proveedores internacionales

## Ejemplos de Uso

### Crear un Proveedor

```http
POST /api/v1/proveedores/
Content-Type: application/json
Authorization: Bearer {token}

{
  "nombre": "Proveedor ABC SRL",
  "tipo_identificacion": "RNC",
  "numero_identificacion": "123456789",
  "tipo_contribuyente": "JURIDICA",
  "telefono": "809-555-1234",
  "correo_electronico": "contacto@proveedorabc.com",
  "direccion": "Calle Principal #123, Santo Domingo",
  "es_internacional": false,
  "activo": true
}
```

### Obtener Historial de Compras de un Proveedor

```http
GET /api/v1/proveedores/1/historial_compras/
Authorization: Bearer {token}
```

**Respuesta:**
```json
{
  "proveedor": "Proveedor ABC SRL",
  "total_compras": 10,
  "total_comprado": 50000.00,
  "total_pagado": 30000.00,
  "total_pendiente": 20000.00,
  "compras": [
    {
      "id": 1,
      "numero_factura": "FAC-001",
      "ncf": "B0100000001",
      "fecha_compra": "2024-01-15",
      "total": 5000.00,
      "estado": "PAGADA",
      "monto_pagado": 5000.00,
      "monto_pendiente": 0.00,
      "tipo_gasto": "02"
    }
  ]
}
```

### Obtener Resumen de un Proveedor

```http
GET /api/v1/proveedores/1/resumen/
Authorization: Bearer {token}
```

**Respuesta:**
```json
{
  "proveedor": {
    "id": 1,
    "nombre": "Proveedor ABC SRL",
    "tipo_contribuyente": "JURIDICA",
    ...
  },
  "estadisticas": {
    "total_compras": 10,
    "total_comprado": 50000.00,
    "total_pagado": 30000.00,
    "total_pendiente": 20000.00,
    "total_ordenes": 5,
    "total_ordenado": 25000.00
  }
}
```

### Buscar Proveedores

```http
GET /api/v1/proveedores/?search=ABC
Authorization: Bearer {token}
```

### Filtrar Proveedores Activos

```http
GET /api/v1/proveedores/?activo=true
Authorization: Bearer {token}
```

### Filtrar por Tipo de Contribuyente

```http
GET /api/v1/proveedores/?tipo_contribuyente=JURIDICA
Authorization: Bearer {token}
```

## Notas de Implementación

### Cambios Recientes

1. **Campo `empresa` agregado**: El modelo ahora incluye el campo `empresa` como ForeignKey requerido
2. **Restricciones `unique_together` actualizadas**: Ahora incluyen `empresa` para permitir números duplicados entre diferentes empresas
3. **Validaciones mejoradas**: Validación de correo, teléfono y RNC obligatorio
4. **Filtros avanzados**: Filtros por activo, tipo identificación, tipo contribuyente e internacional
5. **Acciones personalizadas**: Historial de compras, órdenes y resumen con estadísticas
6. **Admin configurado**: Modelo registrado en el admin de Django con configuraciones personalizadas

### Dependencias

- `empresas.Empresa`: Modelo de empresa (requerido)
- `compras.Compra`: Para historial de compras
- `compras.OrdenCompra`: Para historial de órdenes

### Permisos

El módulo utiliza `ActionBasedPermission` que requiere:
- Autenticación del usuario
- Permisos específicos según la acción (crear, leer, actualizar, eliminar)

## Próximas Mejoras Sugeridas

1. Agregar validación de límite de crédito antes de crear órdenes de compra
2. Implementar historial de cambios (auditoría completa)
3. Agregar campos adicionales para segmentación de proveedores
4. Implementar reportes de proveedores por tipo de contribuyente
5. Agregar validación de correo electrónico único por empresa
6. Integración con DGII para validación de RNC en tiempo real

