# Módulo de Vendedores

## Descripción General

El módulo de vendedores gestiona la información de los vendedores del sistema, incluyendo sus datos de contacto, comisiones, y su relación con usuarios del sistema. Este módulo es fundamental para el proceso de ventas, asignación de clientes y cálculo de comisiones.

## Estructura del Módulo

### Modelos

#### Vendedor

Información completa de los vendedores del sistema.

**Campos:**
- `empresa` (ForeignKey): Empresa a la que pertenece el vendedor (requerido)
- `uuid` (UUIDField): Identificador único universal
- `nombre` (CharField, max_length=200): Nombre del vendedor (requerido)
- `cedula` (CharField, max_length=20): Cédula del vendedor (opcional)
- `telefono` (CharField, max_length=20): Teléfono de contacto (opcional)
- `correo` (EmailField): Correo electrónico (opcional)
- `comision_porcentaje` (DecimalField): Porcentaje de comisión por ventas (0-100, default: 0.00)
- `usuario` (OneToOneField): Usuario del sistema asociado (opcional)
- `activo` (BooleanField): Indica si el vendedor está activo (default: True)
- `fecha_creacion` (DateTimeField): Fecha de creación (auto)
- `fecha_actualizacion` (DateTimeField): Fecha de última actualización (auto)
- `usuario_creacion` (ForeignKey): Usuario que creó el registro
- `usuario_modificacion` (ForeignKey): Usuario que modificó el registro
- `idempotency_key` (CharField): Clave para operaciones idempotentes

**Restricciones:**
- `unique_together`: (`empresa`, `cedula`) - No puede haber dos vendedores con la misma cédula en la misma empresa
- Validación: `comision_porcentaje` debe estar entre 0 y 100

**Relaciones:**
- Relación inversa con `Cliente` a través de `vendedor_asignado` (related_name: `clientes`)
- Relación inversa con `Factura` a través de `vendedor` (related_name: `facturas`)
- Relación inversa con `CotizacionCliente` a través de `vendedor` (related_name: `cotizaciones`)

### Serializers

#### VendedorSerializer

Serializer para `Vendedor` con todos los campos. Incluye:

**Campos calculados (read-only):**
- `empresa_nombre`: Nombre de la empresa a la que pertenece el vendedor
- `usuario_username`: Username del usuario asociado (si existe)
- `total_clientes`: Número total de clientes asignados al vendedor
- `total_ventas`: Monto total de ventas del vendedor

**Validaciones:**
- Correo electrónico válido
- Teléfono con formato válido (10-15 dígitos)
- Comisión porcentaje entre 0-100
- Cédula única por empresa

### Viewsets (API Endpoints)

#### VendedorViewSet

**Endpoint:** `/api/v1/vendedores/`

**Características:**
- Hereda de `IdempotencyMixin` para operaciones idempotentes
- Filtrado automático por empresa del usuario autenticado
- Búsqueda por nombre, cédula, teléfono y correo
- Ordenamiento por nombre, fecha de creación y comisión porcentaje
- Requiere autenticación y permisos basados en acciones

**Métodos HTTP:**
- `GET /api/v1/vendedores/` - Listar vendedores
- `POST /api/v1/vendedores/` - Crear vendedor
- `GET /api/v1/vendedores/{id}/` - Obtener vendedor
- `PUT /api/v1/vendedores/{id}/` - Actualizar vendedor completo
- `PATCH /api/v1/vendedores/{id}/` - Actualizar vendedor parcial
- `DELETE /api/v1/vendedores/{id}/` - Eliminar vendedor

**Filtros de consulta:**
- `?activo=true/false` - Filtrar por estado activo
- `?usuario={id}` - Filtrar por usuario asociado
- `?search={texto}` - Búsqueda en nombre, cédula, teléfono y correo
- `?ordering={campo}` - Ordenar por nombre, fecha_creacion, comision_porcentaje

**Acciones Personalizadas:**
- `GET /api/v1/vendedores/{id}/estadisticas/` - Obtener estadísticas del vendedor
- `GET /api/v1/vendedores/{id}/ventas/` - Listar ventas del vendedor
- `GET /api/v1/vendedores/{id}/cotizaciones/` - Listar cotizaciones del vendedor
- `GET /api/v1/vendedores/{id}/clientes/` - Listar clientes asignados al vendedor
- `GET /api/v1/vendedores/{id}/comisiones/` - Calcular comisiones del vendedor en un período

### Admin de Django

El modelo está registrado en el admin de Django con configuración personalizada:

#### VendedorAdmin
- Lista: nombre, cédula, teléfono, correo, comisión porcentaje, usuario, activo, empresa, fecha de creación
- Filtros: activo, empresa, fecha de creación
- Búsqueda: nombre, cédula, teléfono, correo, usuario, empresa
- Campos de solo lectura: uuid, idempotency_key, fechas, usuarios
- Fieldsets organizados por secciones: Información Básica, Identificación, Contacto, Configuración, Auditoría

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
- Los vendedores están vinculados a facturas y cotizaciones
- Cálculo automático de comisiones basado en porcentaje configurado
- Acciones personalizadas para consultar estadísticas y historial

### Relación con Usuarios
- Un vendedor puede estar asociado a un usuario del sistema (OneToOneField)
- Permite que usuarios del sistema actúen como vendedores
- La relación es opcional para permitir vendedores externos

## Ejemplos de Uso

### Crear un Vendedor

```http
POST /api/v1/vendedores/
Content-Type: application/json
Authorization: Bearer {token}

{
  "nombre": "Juan Pérez",
  "cedula": "001-1234567-8",
  "telefono": "809-555-1234",
  "correo": "juan.perez@empresa.com",
  "comision_porcentaje": 5.00,
  "usuario": 1,
  "activo": true
}
```

### Obtener Estadísticas de un Vendedor

```http
GET /api/v1/vendedores/1/estadisticas/
Authorization: Bearer {token}
```

**Respuesta:**
```json
{
  "vendedor": {
    "id": 1,
    "nombre": "Juan Pérez",
    "comision_porcentaje": "5.00",
    ...
  },
  "estadisticas": {
    "total_ventas": 25,
    "monto_total_ventas": 150000.00,
    "comision_porcentaje": 5.00,
    "monto_comisiones": 7500.00,
    "total_cotizaciones": 10,
    "cotizaciones_aprobadas": 8,
    "total_clientes": 15
  }
}
```

### Obtener Ventas de un Vendedor

```http
GET /api/v1/vendedores/1/ventas/
Authorization: Bearer {token}
```

**Respuesta:**
```json
{
  "vendedor": "Juan Pérez",
  "total_ventas": 25,
  "monto_total": 150000.00,
  "ventas": [
    {
      "id": 1,
      "numero": "FAC-001",
      "ncf": "B0100000001",
      "cliente": "Empresa ABC",
      "fecha": "2024-01-15",
      "total": 5000.00,
      "estado": "PAGADA",
      "tipo_venta": "CONTADO"
    },
    ...
  ]
}
```

### Calcular Comisiones en un Período

```http
GET /api/v1/vendedores/1/comisiones/?fecha_inicio=2024-01-01&fecha_fin=2024-01-31
Authorization: Bearer {token}
```

**Respuesta:**
```json
{
  "vendedor": "Juan Pérez",
  "comision_porcentaje": 5.00,
  "periodo": {
    "fecha_inicio": "2024-01-01",
    "fecha_fin": "2024-01-31"
  },
  "resumen": {
    "total_ventas": 10,
    "monto_total_ventas": 50000.00,
    "monto_total_comisiones": 2500.00
  },
  "detalle": [
    {
      "factura_id": 1,
      "numero_factura": "FAC-001",
      "fecha": "2024-01-15",
      "cliente": "Empresa ABC",
      "monto_venta": 5000.00,
      "comision": 250.00
    },
    ...
  ]
}
```

### Listar Clientes Asignados

```http
GET /api/v1/vendedores/1/clientes/
Authorization: Bearer {token}
```

### Buscar Vendedores

```http
GET /api/v1/vendedores/?search=Pérez
Authorization: Bearer {token}
```

### Filtrar Vendedores Activos

```http
GET /api/v1/vendedores/?activo=true
Authorization: Bearer {token}
```

## Notas de Implementación

### Cambios Recientes

1. **Campo `empresa` agregado**: El modelo ahora incluye el campo `empresa` como ForeignKey requerido
2. **Campo `uuid` agregado**: Identificador único universal para cada vendedor
3. **Campos de auditoría agregados**: `usuario_creacion` y `usuario_modificacion`
4. **Restricciones `unique_together` actualizadas**: Ahora incluyen `empresa` para permitir cédulas duplicadas entre diferentes empresas
5. **Validadores agregados**: `comision_porcentaje` ahora tiene validadores MinValueValidator y MaxValueValidator
6. **Serializer mejorado**: Incluye campos calculados y validaciones personalizadas
7. **ViewSet mejorado**: Incluye filtrado por empresa, filtros específicos y acciones personalizadas
8. **Admin configurado**: El modelo está registrado en el admin de Django con configuración personalizada

### Dependencias

- `empresas.Empresa`: Modelo de empresa (requerido)
- `usuarios.User`: Modelo de usuario (opcional, para relación OneToOne)
- `clientes.Cliente`: Para relación inversa con clientes asignados
- `ventas.Factura`: Para estadísticas de ventas y cálculo de comisiones
- `ventas.CotizacionCliente`: Para estadísticas de cotizaciones

### Permisos

El módulo utiliza `ActionBasedPermission` que requiere:
- Autenticación del usuario
- Permisos específicos según la acción (crear, leer, actualizar, eliminar)

### Cálculo de Comisiones

Las comisiones se calculan multiplicando el monto total de ventas por el porcentaje de comisión del vendedor:
```
Comisión = (Monto Total Ventas × Comisión Porcentaje) / 100
```

Solo se consideran facturas con estado `PAGADA` o `PAGADA_PARCIAL` para el cálculo de comisiones.

## Próximas Mejoras Sugeridas

1. Agregar historial de cambios de comisiones
2. Implementar diferentes tipos de comisiones (fija, por volumen, escalonada)
3. Agregar reportes de rendimiento de vendedores
4. Implementar metas y objetivos por vendedor
5. Agregar validación de cédula dominicana
6. Implementar notificaciones cuando se asignen nuevos clientes a un vendedor
7. Agregar campo de foto del vendedor
8. Implementar ranking de vendedores por ventas

