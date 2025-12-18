# Módulo de Compras

## Descripción General

El módulo de compras gestiona todo el ciclo de compras desde la solicitud de cotización hasta el registro de facturas de proveedores y gastos operativos. Incluye integración con el módulo de inventario para registrar automáticamente las entradas de productos almacenables.

## Estructura del Módulo

### Modelos Principales

#### SolicitudCotizacionProveedor

Representa una solicitud de cotización enviada a un proveedor.

**Campos:**
- `empresa` (ForeignKey): Empresa a la que pertenece la solicitud (requerido)
- `proveedor` (ForeignKey): Proveedor al que se solicita la cotización (requerido)
- `fecha_solicitud` (DateField): Fecha de la solicitud (auto_now_add)
- `estado` (CharField): Estado de la solicitud (PENDIENTE, ENVIADA, RECIBIDA, CANCELADA)
- `detalles` (TextField): Descripción de productos/servicios solicitados
- `uuid` (UUIDField): Identificador único universal
- `idempotency_key` (CharField): Clave para operaciones idempotentes
- `fecha_creacion` (DateTimeField): Fecha de creación (auto)
- `fecha_actualizacion` (DateTimeField): Fecha de última actualización (auto)
- `usuario_creacion` (ForeignKey): Usuario que creó el registro
- `usuario_modificacion` (ForeignKey): Usuario que modificó el registro

**Estados:**
- `PENDIENTE`: Solicitud creada pero no enviada
- `ENVIADA`: Solicitud enviada al proveedor
- `RECIBIDA`: Cotización recibida del proveedor
- `CANCELADA`: Solicitud cancelada

#### OrdenCompra

Representa una orden de compra formal enviada a un proveedor.

**Campos:**
- `empresa` (ForeignKey): Empresa a la que pertenece la orden (requerido)
- `proveedor` (ForeignKey): Proveedor de la orden (requerido)
- `fecha_emision` (DateField): Fecha de emisión (auto_now_add)
- `fecha_entrega_esperada` (DateField): Fecha esperada de entrega (opcional)
- `estado` (CharField): Estado de la orden (BORRADOR, APROBADA, ENVIADA, RECIBIDA_PARCIAL, RECIBIDA_TOTAL, CANCELADA)
- `tasa_cambio` (DecimalField): Tasa de cambio para moneda extranjera (default: 1.0000)
- `condiciones_pago` (CharField): Condiciones de pago (opcional)
- `observaciones` (TextField): Observaciones adicionales
- `subtotal` (DecimalField): Subtotal de la orden
- `impuestos` (DecimalField): Total de impuestos
- `descuentos` (DecimalField): Total de descuentos
- `total` (DecimalField): Total de la orden
- `usuario_creacion` (ForeignKey): Usuario que creó la orden
- `usuario_aprobacion` (ForeignKey): Usuario que aprobó la orden
- `usuario_modificacion` (ForeignKey): Usuario que modificó la orden
- `fecha_creacion` (DateTimeField): Fecha de creación (auto)
- `fecha_actualizacion` (DateTimeField): Fecha de última actualización (auto)
- `uuid` (UUIDField): Identificador único universal
- `idempotency_key` (CharField): Clave para operaciones idempotentes

**Estados:**
- `BORRADOR`: Orden en borrador
- `APROBADA`: Orden aprobada para envío
- `ENVIADA`: Orden enviada al proveedor
- `RECIBIDA_PARCIAL`: Orden recibida parcialmente
- `RECIBIDA_TOTAL`: Orden recibida completamente
- `CANCELADA`: Orden cancelada

#### DetalleOrdenCompra

Detalle de productos/servicios en una orden de compra.

**Campos:**
- `orden` (ForeignKey): Orden de compra relacionada
- `producto` (ForeignKey): Producto solicitado
- `cantidad` (DecimalField): Cantidad solicitada
- `cantidad_recibida` (DecimalField): Cantidad recibida (default: 0)
- `costo_unitario` (DecimalField): Costo unitario
- `impuesto` (DecimalField): Impuesto de la línea
- `descuento` (DecimalField): Descuento de la línea
- `tipo_linea` (CharField): Tipo de línea (ALMACENABLE, GASTO, ACTIVO)

**Propiedades calculadas:**
- `subtotal`: (cantidad * costo_unitario) - descuento + impuesto

#### Compra

Representa una factura de compra recibida de un proveedor.

**Campos:**
- `empresa` (ForeignKey): Empresa a la que pertenece la compra (requerido)
- `orden_compra` (ForeignKey): Orden de compra relacionada (opcional)
- `proveedor` (ForeignKey): Proveedor de la factura (requerido)
- `tipo_gasto` (CharField): Tipo de gasto según DGII 606 (01-11)
- `fecha_compra` (DateField): Fecha de la factura del proveedor
- `numero_factura_proveedor` (CharField): Número de factura del proveedor
- `numero_ncf` (CharField): Número de Comprobante Fiscal (opcional)
- `ncf_modificado` (CharField): NCF afectado por Nota de Crédito/Débito (opcional)
- `estado` (CharField): Estado de la compra (REGISTRADA, CXP, PAGADA, ANULADA)
- `tasa_cambio` (DecimalField): Tasa de cambio para moneda extranjera (default: 1.0000)
- `subtotal` (DecimalField): Subtotal de la compra
- `impuestos` (DecimalField): Total de impuestos
- `itbis_facturado` (DecimalField): ITBIS facturado (DGII)
- `itbis_retenido` (DecimalField): ITBIS retenido (DGII)
- `itbis_llevado_al_costo` (DecimalField): ITBIS llevado al costo (DGII)
- `isr_retenido` (DecimalField): Retención de Renta (DGII)
- `descuentos` (DecimalField): Total de descuentos
- `total` (DecimalField): Total de la compra
- `monto_pagado` (DecimalField): Monto pagado hasta la fecha
- `fecha_registro` (DateTimeField): Fecha de registro en el sistema (auto_now_add)
- `fecha_creacion` (DateTimeField): Fecha de creación (auto)
- `fecha_actualizacion` (DateTimeField): Fecha de última actualización (auto)
- `usuario_creacion` (ForeignKey): Usuario que creó el registro
- `usuario_modificacion` (ForeignKey): Usuario que modificó el registro
- `uuid` (UUIDField): Identificador único universal
- `idempotency_key` (CharField): Clave para operaciones idempotentes

**Estados:**
- `REGISTRADA`: Compra ingresada en el sistema
- `CXP`: Compra procesada y en cuentas por pagar
- `PAGADA`: Compra pagada completamente
- `ANULADA`: Compra anulada

**Tipos de Gasto (DGII 606):**
- `01`: Gastos de Personal
- `02`: Gastos por Trabajos, Suministros y Servicios
- `03`: Arrendamientos
- `04`: Gastos de Activos Fijos
- `05`: Gastos de Representación
- `06`: Otras Deducciones Admitidas
- `07`: Gastos Financieros
- `08`: Gastos Extraordinarios
- `09`: Compras y Gastos que forman parte del Costo de Venta
- `10`: Adquisiciones de Activos
- `11`: Gastos de Seguros

**Restricciones:**
- `unique_together`: (`empresa`, `proveedor`, `numero_factura_proveedor`) - No puede haber dos compras con el mismo número de factura para el mismo proveedor en la misma empresa

#### DetalleCompra

Detalle de productos/servicios en una compra.

**Campos:**
- `compra` (ForeignKey): Compra relacionada
- `producto` (ForeignKey): Producto comprado
- `cantidad` (DecimalField): Cantidad comprada
- `costo_unitario` (DecimalField): Costo unitario
- `impuesto` (DecimalField): Impuesto de la línea
- `descuento` (DecimalField): Descuento de la línea
- `tipo_linea` (CharField): Tipo de línea (ALMACENABLE, GASTO, ACTIVO)

**Auto-detección:**
- Si el producto es nuevo y tiene `tipo_producto`, se auto-detectará el `tipo_linea`:
  - `ALMACENABLE` → `tipo_linea='ALMACENABLE'`
  - `ACTIVO_FIJO` → `tipo_linea='ACTIVO'`
  - Otros → `tipo_linea='GASTO'`

#### Gasto

Gastos operativos que no implican inventario (Luz, Agua, Alquiler, Nómina, etc.).

**Campos:**
- `empresa` (ForeignKey): Empresa a la que pertenece el gasto (requerido)
- `proveedor` (ForeignKey): Proveedor del gasto (opcional, ej: Edesur)
- `descripcion` (CharField): Descripción del gasto
- `categoria` (CharField): Categoría del gasto (ej: Servicios Públicos, Nómina, Mantenimiento)
- `fecha_gasto` (DateField): Fecha del gasto
- `numero_factura` (CharField): Número de factura (opcional)
- `numero_ncf` (CharField): Número de Comprobante Fiscal (opcional)
- `tasa_cambio` (DecimalField): Tasa de cambio para moneda extranjera (default: 1.0000)
- `subtotal` (DecimalField): Subtotal del gasto
- `impuestos` (DecimalField): Total de impuestos
- `total` (DecimalField): Total del gasto
- `estado` (CharField): Estado del gasto (PENDIENTE, PAGADO)
- `usuario_creacion` (ForeignKey): Usuario que creó el registro
- `usuario_modificacion` (ForeignKey): Usuario que modificó el registro
- `fecha_creacion` (DateTimeField): Fecha de creación (auto)
- `fecha_actualizacion` (DateTimeField): Fecha de última actualización (auto)
- `uuid` (UUIDField): Identificador único universal
- `idempotency_key` (CharField): Clave para operaciones idempotentes

**Estados:**
- `PENDIENTE`: Gasto pendiente de pago
- `PAGADO`: Gasto pagado

### Serializers

#### SolicitudCotizacionProveedorSerializer

Serializer para `SolicitudCotizacionProveedor` con todos los campos. Incluye:
- `proveedor_nombre`: Campo calculado que muestra el nombre del proveedor (read-only)
- `empresa_nombre`: Campo calculado que muestra el nombre de la empresa (read-only)
- Validación: El proveedor debe pertenecer a la misma empresa

**Read-only fields:** `id`, `uuid`, `fecha_creacion`, `fecha_actualizacion`, `usuario_creacion`, `usuario_modificacion`, `empresa`

#### OrdenCompraSerializer

Serializer para `OrdenCompra` con todos los campos. Incluye:
- `proveedor_nombre`: Campo calculado que muestra el nombre del proveedor (read-only)
- `empresa_nombre`: Campo calculado que muestra el nombre de la empresa (read-only)
- `detalles`: Lista de detalles de la orden (read-only)
- Validación: El proveedor debe pertenecer a la misma empresa

**Read-only fields:** `id`, `uuid`, `fecha_creacion`, `fecha_actualizacion`, `usuario_creacion`, `usuario_modificacion`, `usuario_aprobacion`, `empresa`

#### DetalleOrdenCompraSerializer

Serializer para `DetalleOrdenCompra` con todos los campos. Incluye:
- `producto_nombre`: Campo calculado que muestra el nombre del producto (read-only)
- `subtotal`: Campo calculado (read-only)

**Read-only fields:** `id`, `subtotal`

#### CompraSerializer

Serializer para `Compra` con todos los campos. Incluye:
- `proveedor_nombre`: Campo calculado que muestra el nombre del proveedor (read-only)
- `empresa_nombre`: Campo calculado que muestra el nombre de la empresa (read-only)
- `detalles`: Lista de detalles de la compra (read-only)
- Validación: El proveedor debe pertenecer a la misma empresa
- Validación: Unicidad de `numero_factura_proveedor` por empresa y proveedor

**Read-only fields:** `id`, `uuid`, `fecha_creacion`, `fecha_actualizacion`, `fecha_registro`, `usuario_creacion`, `usuario_modificacion`, `empresa`

#### DetalleCompraSerializer

Serializer para `DetalleCompra` con todos los campos. Incluye:
- `producto_nombre`: Campo calculado que muestra el nombre del producto (read-only)

**Read-only fields:** `id`

#### GastoSerializer

Serializer para `Gasto` con todos los campos. Incluye:
- `proveedor_nombre`: Campo calculado que muestra el nombre del proveedor (read-only)
- `empresa_nombre`: Campo calculado que muestra el nombre de la empresa (read-only)
- Validación: El proveedor debe pertenecer a la misma empresa si se proporciona

**Read-only fields:** `id`, `uuid`, `fecha_creacion`, `fecha_actualizacion`, `usuario_creacion`, `usuario_modificacion`, `empresa`

### ViewSets (API Endpoints)

#### SolicitudCotizacionProveedorViewSet

**Endpoint:** `/api/v1/compras/solicitudes/`

**Características:**
- Hereda de `IdempotencyMixin` para operaciones idempotentes
- Filtrado automático por empresa del usuario autenticado
- Búsqueda por nombre del proveedor y detalles
- Ordenamiento por fecha de solicitud y estado
- Filtros: `?estado={estado}`, `?proveedor={id}`

**Métodos HTTP:**
- `GET /api/v1/compras/solicitudes/` - Listar solicitudes
- `POST /api/v1/compras/solicitudes/` - Crear solicitud
- `GET /api/v1/compras/solicitudes/{id}/` - Obtener solicitud
- `PUT /api/v1/compras/solicitudes/{id}/` - Actualizar solicitud completa
- `PATCH /api/v1/compras/solicitudes/{id}/` - Actualizar solicitud parcial
- `DELETE /api/v1/compras/solicitudes/{id}/` - Eliminar solicitud

#### OrdenCompraViewSet

**Endpoint:** `/api/v1/compras/ordenes/`

**Características:**
- Hereda de `IdempotencyMixin` para operaciones idempotentes
- Filtrado automático por empresa del usuario autenticado
- Búsqueda por nombre del proveedor y observaciones
- Ordenamiento por fecha de emisión, estado y total
- Filtros: `?estado={estado}`, `?proveedor={id}`

**Métodos HTTP:**
- `GET /api/v1/compras/ordenes/` - Listar órdenes
- `POST /api/v1/compras/ordenes/` - Crear orden
- `GET /api/v1/compras/ordenes/{id}/` - Obtener orden
- `PUT /api/v1/compras/ordenes/{id}/` - Actualizar orden completa
- `PATCH /api/v1/compras/ordenes/{id}/` - Actualizar orden parcial
- `DELETE /api/v1/compras/ordenes/{id}/` - Eliminar orden

**Acciones Personalizadas:**
- `POST /api/v1/compras/ordenes/{id}/aprobar/` - Aprueba una orden de compra (cambia estado a APROBADA)
- `POST /api/v1/compras/ordenes/{id}/enviar/` - Marca la orden como enviada al proveedor
- `POST /api/v1/compras/ordenes/{id}/recibir/` - Recibe una orden con cantidades recibidas
  - Body: `{"detalles_recibidos": {detalle_id: cantidad_recibida}}`
- `POST /api/v1/compras/ordenes/{id}/cancelar/` - Cancela una orden de compra

#### CompraViewSet

**Endpoint:** `/api/v1/compras/facturas/`

**Características:**
- Hereda de `IdempotencyMixin` para operaciones idempotentes
- Filtrado automático por empresa del usuario autenticado
- Búsqueda por nombre del proveedor, número de factura y NCF
- Ordenamiento por fecha de compra, fecha de registro, total y estado
- Filtros: `?estado={estado}`, `?proveedor={id}`, `?fecha_desde={fecha}`, `?fecha_hasta={fecha}`

**Métodos HTTP:**
- `GET /api/v1/compras/facturas/` - Listar compras
- `POST /api/v1/compras/facturas/` - Crear compra
- `GET /api/v1/compras/facturas/{id}/` - Obtener compra
- `PUT /api/v1/compras/facturas/{id}/` - Actualizar compra completa
- `PATCH /api/v1/compras/facturas/{id}/` - Actualizar compra parcial
- `DELETE /api/v1/compras/facturas/{id}/` - Eliminar compra

**Acciones Personalizadas:**
- `POST /api/v1/compras/facturas/{id}/procesar/` - Procesa una compra registrando movimientos de inventario
  - Body opcional: `{"almacen_id": {id}}` - Si no se proporciona, usa el primer almacén activo de la empresa
  - Solo registra movimientos para productos con `tipo_linea='ALMACENABLE'`
  - Cambia el estado de la compra a `CXP`
- `POST /api/v1/compras/facturas/{id}/anular/` - Anula una compra y revierte movimientos de inventario
  - No se puede anular una compra pagada
  - Crea movimientos de salida para revertir las entradas de inventario

#### GastoViewSet

**Endpoint:** `/api/v1/compras/gastos/`

**Características:**
- Hereda de `IdempotencyMixin` para operaciones idempotentes
- Filtrado automático por empresa del usuario autenticado
- Búsqueda por descripción, categoría, número de factura y nombre del proveedor
- Ordenamiento por fecha de gasto, fecha de creación, total y estado
- Filtros: `?estado={estado}`, `?categoria={categoria}`, `?proveedor={id}`, `?fecha_desde={fecha}`, `?fecha_hasta={fecha}`

**Métodos HTTP:**
- `GET /api/v1/compras/gastos/` - Listar gastos
- `POST /api/v1/compras/gastos/` - Crear gasto
- `GET /api/v1/compras/gastos/{id}/` - Obtener gasto
- `PUT /api/v1/compras/gastos/{id}/` - Actualizar gasto completo
- `PATCH /api/v1/compras/gastos/{id}/` - Actualizar gasto parcial
- `DELETE /api/v1/compras/gastos/{id}/` - Eliminar gasto

**Acciones Personalizadas:**
- `POST /api/v1/compras/gastos/{id}/marcar_pagado/` - Marca un gasto como pagado

### Servicios de Negocio

#### ServicioCompras

Servicio principal para operaciones de compras con integración a inventario.

**Métodos:**

##### `procesar_compra(compra, usuario, almacen=None)`

Procesa una compra registrando movimientos de inventario para productos almacenables.

**Parámetros:**
- `compra`: Instancia de `Compra`
- `usuario`: Usuario que procesa la compra
- `almacen`: Almacén donde se recibirá el inventario (opcional, usa el primero activo de la empresa si no se proporciona)

**Comportamiento:**
- Valida que la compra esté en estado `REGISTRADA`
- Obtiene o crea el almacén si no se proporciona
- Itera sobre los detalles de la compra
- Para cada detalle con `tipo_linea='ALMACENABLE'`, registra un movimiento de inventario con:
  - `tipo_movimiento='ENTRADA_COMPRA'`
  - `tipo_documento_origen='COMPRA'`
  - `documento_origen_id=compra.id`
  - `referencia=f"COMP-{compra.numero_factura_proveedor}"`
- Cambia el estado de la compra a `CXP`
- Retorna la lista de movimientos registrados

**Excepciones:**
- `ValidationError`: Si la compra no está en estado `REGISTRADA`
- `ValidationError`: Si no hay almacenes activos disponibles
- `ValidationError`: Si el almacén no pertenece a la empresa de la compra
- `ValidationError`: Si hay error al registrar algún movimiento

##### `anular_compra(compra, usuario)`

Anula una compra y revierte los movimientos de inventario si existen.

**Parámetros:**
- `compra`: Instancia de `Compra`
- `usuario`: Usuario que anula la compra

**Comportamiento:**
- Valida que la compra no esté ya anulada o pagada
- Busca movimientos de inventario relacionados con la compra
- Para cada movimiento encontrado, crea un movimiento de salida para revertirlo:
  - `tipo_movimiento='SALIDA_AJUSTE'`
  - `referencia=f"ANUL-{compra.numero_factura_proveedor}"`
- Cambia el estado de la compra a `ANULADA`

**Excepciones:**
- `ValidationError`: Si la compra ya está anulada
- `ValidationError`: Si la compra está pagada
- `ValidationError`: Si hay error al revertir algún movimiento

##### `recibir_orden_compra(orden_compra, detalles_recibidos, usuario, almacen=None)`

Recibe una orden de compra actualizando las cantidades recibidas.

**Parámetros:**
- `orden_compra`: Instancia de `OrdenCompra`
- `detalles_recibidos`: Dict con `{detalle_id: cantidad_recibida}`
- `usuario`: Usuario que recibe la orden
- `almacen`: Almacén donde se recibirá (opcional, no usado actualmente)

**Comportamiento:**
- Valida que la orden esté en estado apropiado (APROBADA, ENVIADA, RECIBIDA_PARCIAL)
- Actualiza las cantidades recibidas en cada detalle
- Valida que las cantidades recibidas no excedan las solicitadas
- Actualiza el estado de la orden según las cantidades:
  - `RECIBIDA_TOTAL`: Si todas las cantidades fueron recibidas
  - `RECIBIDA_PARCIAL`: Si solo algunas cantidades fueron recibidas
- Retorna la orden actualizada

**Excepciones:**
- `ValidationError`: Si la orden no está en estado apropiado
- `ValidationError`: Si alguna cantidad recibida excede la solicitada
- `ValidationError`: Si no se recibió ninguna cantidad

### Django Admin

Todos los modelos están registrados en el admin de Django con configuraciones personalizadas:

#### SolicitudCotizacionProveedorAdmin
- Lista: proveedor, empresa, fecha de solicitud, estado, usuario de creación, fecha de creación
- Filtros: estado, empresa, fecha de solicitud
- Búsqueda: nombre del proveedor, detalles
- Campos de solo lectura: uuid, idempotency_key, fechas, usuarios

#### OrdenCompraAdmin
- Lista: ID, proveedor, empresa, fecha de emisión, estado, total, usuario de creación, usuario de aprobación
- Filtros: estado, empresa, fecha de emisión
- Búsqueda: nombre del proveedor, observaciones
- Inline: `DetalleOrdenCompraInline` para gestionar detalles
- Campos de solo lectura: uuid, idempotency_key, fechas, usuarios

#### CompraAdmin
- Lista: número de factura, proveedor, empresa, fecha de compra, estado, total, monto pagado, usuario de creación
- Filtros: estado, empresa, tipo de gasto, fecha de compra, fecha de registro
- Búsqueda: número de factura, NCF, nombre del proveedor
- Inline: `DetalleCompraInline` para gestionar detalles
- Campos de solo lectura: uuid, idempotency_key, fechas, usuarios

#### GastoAdmin
- Lista: descripción, categoría, empresa, proveedor, fecha de gasto, total, estado, usuario de creación
- Filtros: estado, categoría, empresa, fecha de gasto
- Búsqueda: descripción, categoría, número de factura, nombre del proveedor
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
- Soporte para idempotencia mediante `idempotency_key`

### Integración con Inventario
- Las compras pueden registrar automáticamente movimientos de inventario
- Solo se registran movimientos para productos con `tipo_linea='ALMACENABLE'`
- Los movimientos incluyen referencia al documento origen (compra)
- Soporte para anulación y reversión de movimientos

### Gestión de Estados
- Flujo de estados para órdenes de compra: BORRADOR → APROBADA → ENVIADA → RECIBIDA
- Flujo de estados para compras: REGISTRADA → CXP → PAGADA
- Soporte para cancelación y anulación

### Cumplimiento Fiscal (DGII)
- Campos específicos para retenciones ITBIS e ISR
- Tipos de gasto según DGII 606
- Soporte para NCF y NCF modificado

## Ejemplos de Uso

### Crear una Solicitud de Cotización

```http
POST /api/v1/compras/solicitudes/
Content-Type: application/json
Authorization: Bearer {token}

{
  "proveedor": 1,
  "detalles": "Solicito cotización para 100 unidades del producto ABC",
  "estado": "PENDIENTE"
}
```

### Crear una Orden de Compra

```http
POST /api/v1/compras/ordenes/
Content-Type: application/json
Authorization: Bearer {token}

{
  "proveedor": 1,
  "fecha_entrega_esperada": "2024-12-31",
  "condiciones_pago": "30 días",
  "observaciones": "Urgente",
  "subtotal": 10000.00,
  "impuestos": 1800.00,
  "descuentos": 500.00,
  "total": 11300.00
}
```

### Aprobar una Orden de Compra

```http
POST /api/v1/compras/ordenes/1/aprobar/
Authorization: Bearer {token}
```

### Recibir una Orden de Compra

```http
POST /api/v1/compras/ordenes/1/recibir/
Content-Type: application/json
Authorization: Bearer {token}

{
  "detalles_recibidos": {
    "1": 50.00,
    "2": 30.00
  }
}
```

### Crear una Compra

```http
POST /api/v1/compras/facturas/
Content-Type: application/json
Authorization: Bearer {token}

{
  "proveedor": 1,
  "orden_compra": 1,
  "tipo_gasto": "02",
  "fecha_compra": "2024-01-15",
  "numero_factura_proveedor": "FAC-001",
  "numero_ncf": "B0100000001",
  "subtotal": 10000.00,
  "impuestos": 1800.00,
  "itbis_facturado": 1800.00,
  "descuentos": 500.00,
  "total": 11300.00
}
```

### Procesar una Compra (Registrar en Inventario)

```http
POST /api/v1/compras/facturas/1/procesar/
Content-Type: application/json
Authorization: Bearer {token}

{
  "almacen_id": 1
}
```

### Anular una Compra

```http
POST /api/v1/compras/facturas/1/anular/
Authorization: Bearer {token}
```

### Crear un Gasto

```http
POST /api/v1/compras/gastos/
Content-Type: application/json
Authorization: Bearer {token}

{
  "proveedor": 2,
  "descripcion": "Servicio de luz - Enero 2024",
  "categoria": "Servicios Públicos",
  "fecha_gasto": "2024-01-31",
  "numero_factura": "EDE-001",
  "numero_ncf": "B0100000002",
  "subtotal": 5000.00,
  "impuestos": 900.00,
  "total": 5900.00,
  "estado": "PENDIENTE"
}
```

### Filtrar Compras por Fecha

```http
GET /api/v1/compras/facturas/?fecha_desde=2024-01-01&fecha_hasta=2024-01-31
Authorization: Bearer {token}
```

## Notas de Implementación

### Cambios Recientes

1. **Campo `empresa` agregado**: Todos los modelos principales ahora incluyen el campo `empresa` como ForeignKey
2. **Campos de auditoría completos**: Se agregaron `usuario_modificacion`, `fecha_creacion`, `fecha_actualizacion` a todos los modelos
3. **Restricciones `unique_together` actualizadas**: `Compra` ahora incluye `empresa` en su constraint de unicidad
4. **Servicios de negocio**: Se creó `ServicioCompras` para manejar la lógica de procesamiento y anulación
5. **Integración con inventario**: Las compras pueden registrar automáticamente movimientos de inventario
6. **ViewSet de Gasto**: Se creó `GastoViewSet` para gestionar gastos operativos
7. **Acciones personalizadas**: Se agregaron acciones para aprobar, enviar, recibir y cancelar órdenes, y procesar/anular compras

### Dependencias

- `empresas.Empresa`: Modelo de empresa (requerido)
- `proveedores.Proveedor`: Modelo de proveedor (requerido)
- `productos.Producto`: Modelo de producto (requerido)
- `inventario.ServicioInventario`: Para registrar movimientos de inventario
- `inventario.Almacen`: Para almacenes donde se reciben productos

### Permisos

El módulo utiliza `ActionBasedPermission` que requiere:
- Autenticación del usuario
- Permisos específicos según la acción (crear, leer, actualizar, eliminar)

### Transacciones

Las operaciones críticas (`procesar_compra`, `anular_compra`, `recibir_orden_compra`) están protegidas con `@transaction.atomic` para garantizar la integridad de los datos.

## Próximas Mejoras Sugeridas

1. Agregar validación de límite de crédito del proveedor antes de crear órdenes
2. Implementar historial de cambios (auditoría completa)
3. Agregar reportes de compras por proveedor y período
4. Implementar notificaciones cuando se reciben órdenes
5. Agregar validación de NCF según formato DGII
6. Implementar cálculo automático de totales en órdenes y compras
7. Agregar soporte para múltiples almacenes en recepción de órdenes
8. Implementar integración con módulo de cuentas por pagar

