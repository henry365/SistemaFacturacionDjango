# Módulo de Inventario

## Descripción General

El módulo de inventario gestiona el control completo de stock, movimientos, reservas, lotes, alertas, transferencias entre almacenes, ajustes y conteos físicos. Es uno de los módulos más complejos del sistema y proporciona trazabilidad completa de todos los movimientos de inventario.

## Estructura del Módulo

### Modelos Principales

#### Almacen

Representa los almacenes o bodegas donde se almacenan los productos.

**Campos:**
- `empresa` (ForeignKey): Empresa a la que pertenece el almacén (requerido)
- `nombre` (CharField, max_length=100): Nombre del almacén (requerido)
- `descripcion` (TextField): Descripción opcional
- `direccion` (TextField): Dirección física del almacén
- `activo` (BooleanField): Indica si el almacén está activo (default: True)
- `uuid` (UUIDField): Identificador único universal
- `idempotency_key` (CharField): Clave para operaciones idempotentes
- `fecha_creacion` (DateTimeField): Fecha de creación (auto)
- `fecha_actualizacion` (DateTimeField): Fecha de última actualización (auto)
- `usuario_creacion` (ForeignKey): Usuario que creó el registro
- `usuario_modificacion` (ForeignKey): Usuario que modificó el registro

**Restricciones:**
- `unique_together`: (`empresa`, `nombre`) - No puede haber dos almacenes con el mismo nombre en la misma empresa

#### InventarioProducto

Representa el inventario de un producto específico en un almacén específico.

**Campos:**
- `empresa` (ForeignKey): Empresa a la que pertenece el inventario (requerido)
- `producto` (ForeignKey): Producto del inventario (requerido)
- `almacen` (ForeignKey): Almacén donde se encuentra el producto (requerido)
- `cantidad_disponible` (DecimalField): Cantidad disponible en stock (default: 0)
- `costo_promedio` (DecimalField): Costo promedio ponderado del producto
- `metodo_valoracion` (CharField): Método de valoración (PROMEDIO, PEPS, UEPS, PRECIO_ESPECIFICO)
- `costo_unitario_actual` (DecimalField): Costo unitario actual según método de valoración
- `stock_minimo` (DecimalField): Cantidad mínima antes de alertar (default: 0)
- `stock_maximo` (DecimalField): Cantidad máxima recomendada (default: 0)
- `punto_reorden` (DecimalField): Punto de reorden automático (default: 0)
- `uuid` (UUIDField): Identificador único universal
- `fecha_creacion` (DateTimeField): Fecha de creación (auto)
- `fecha_actualizacion` (DateTimeField): Fecha de última actualización (auto)
- `usuario_creacion` (ForeignKey): Usuario que creó el registro
- `usuario_modificacion` (ForeignKey): Usuario que modificó el registro

**Propiedades calculadas:**
- `esta_bajo_minimo`: Verifica si el stock está por debajo del mínimo
- `necesita_reorden`: Verifica si necesita reorden
- `stock_reservado`: Stock comprometido en reservas activas
- `stock_disponible_real`: Stock disponible menos reservas
- `valor_inventario`: Valor total del inventario (cantidad * costo promedio)

**Restricciones:**
- `unique_together`: (`producto`, `almacen`) - No puede haber dos registros de inventario para el mismo producto en el mismo almacén

#### MovimientoInventario

Registra todos los movimientos de inventario (entradas, salidas, transferencias, ajustes).

**Campos:**
- `empresa` (ForeignKey): Empresa a la que pertenece el movimiento (requerido)
- `producto` (ForeignKey): Producto del movimiento (requerido)
- `almacen` (ForeignKey): Almacén del movimiento (requerido)
- `tipo_movimiento` (CharField): Tipo de movimiento (ENTRADA_COMPRA, SALIDA_VENTA, TRANSFERENCIA_ENTRADA, etc.)
- `cantidad` (DecimalField): Cantidad del movimiento (requerido, > 0)
- `costo_unitario` (DecimalField): Costo unitario al momento del movimiento
- `fecha` (DateTimeField): Fecha del movimiento (auto_now_add)
- `referencia` (CharField): ID de Compra, Factura, etc. (opcional)
- `lote` (ForeignKey): Lote asociado (opcional)
- `numero_serie` (CharField): Número de serie (opcional)
- `numero_lote_proveedor` (CharField): Número de lote del proveedor (opcional)
- `tipo_documento_origen` (CharField): Tipo de documento origen (COMPRA, FACTURA, AJUSTE, etc.)
- `documento_origen_id` (IntegerField): ID del documento origen
- `usuario` (ForeignKey): Usuario que realizó el movimiento
- `notas` (TextField): Notas adicionales
- `uuid` (UUIDField): Identificador único universal
- `idempotency_key` (CharField): Clave para operaciones idempotentes
- `fecha_actualizacion` (DateTimeField): Fecha de última actualización (auto)
- `usuario_creacion` (ForeignKey): Usuario que creó el registro
- `usuario_modificacion` (ForeignKey): Usuario que modificó el registro

**Tipos de Movimiento:**
- `ENTRADA_COMPRA`: Entrada por compra
- `ENTRADA_AJUSTE`: Entrada por ajuste
- `SALIDA_VENTA`: Salida por venta
- `SALIDA_AJUSTE`: Salida por ajuste
- `TRANSFERENCIA_ENTRADA`: Transferencia (entrada)
- `TRANSFERENCIA_SALIDA`: Transferencia (salida)
- `DEVOLUCION_CLIENTE`: Devolución de cliente
- `DEVOLUCION_PROVEEDOR`: Devolución a proveedor
- Varios tipos de ajustes (DIFERENCIA, DETERIORO, ROBO, DONACION, MUESTRA, PRODUCCION, DESECHO)

#### ReservaStock

Reserva stock para cotizaciones, facturas pendientes, etc.

**Campos:**
- `empresa` (ForeignKey): Empresa a la que pertenece la reserva (requerido)
- `inventario` (ForeignKey): Inventario del producto (requerido)
- `cantidad_reservada` (DecimalField): Cantidad reservada (requerido, > 0)
- `fecha_reserva` (DateTimeField): Fecha de la reserva (auto_now_add)
- `fecha_vencimiento` (DateTimeField): Fecha de vencimiento de la reserva (opcional)
- `estado` (CharField): Estado (PENDIENTE, CONFIRMADA, CANCELADA, VENCIDA)
- `referencia` (CharField): ID de Cotización, Factura, etc.
- `usuario` (ForeignKey): Usuario que realizó la reserva
- `notas` (TextField): Notas adicionales
- `uuid` (UUIDField): Identificador único universal
- `fecha_creacion` (DateTimeField): Fecha de creación (auto)
- `fecha_actualizacion` (DateTimeField): Fecha de última actualización (auto)
- `usuario_creacion` (ForeignKey): Usuario que creó el registro
- `usuario_modificacion` (ForeignKey): Usuario que modificó el registro

#### Lote

Gestiona lotes de productos con fechas de fabricación y vencimiento.

**Campos:**
- `empresa` (ForeignKey): Empresa a la que pertenece el lote (requerido)
- `producto` (ForeignKey): Producto del lote (requerido)
- `almacen` (ForeignKey): Almacén donde se encuentra el lote (requerido)
- `codigo_lote` (CharField): Código de lote/serie (requerido)
- `numero_lote` (CharField): Número de lote (opcional)
- `fecha_fabricacion` (DateField): Fecha de fabricación (opcional)
- `fecha_vencimiento` (DateField): Fecha de vencimiento (opcional)
- `fecha_ingreso` (DateTimeField): Fecha de ingreso al sistema (auto_now_add)
- `cantidad_inicial` (DecimalField): Cantidad inicial del lote (requerido, > 0)
- `cantidad_disponible` (DecimalField): Cantidad disponible del lote (requerido)
- `costo_unitario` (DecimalField): Costo unitario del lote (requerido)
- `estado` (CharField): Estado (DISPONIBLE, BLOQUEADO, VENCIDO, AGOTADO)
- `proveedor` (ForeignKey): Proveedor del lote (opcional)
- `compra` (ForeignKey): Compra asociada (opcional)
- `notas` (TextField): Notas adicionales
- `uuid` (UUIDField): Identificador único universal
- `fecha_creacion` (DateTimeField): Fecha de creación (auto)
- `fecha_actualizacion` (DateTimeField): Fecha de última actualización (auto)
- `usuario_creacion` (ForeignKey): Usuario que creó el registro
- `usuario_modificacion` (ForeignKey): Usuario que modificó el registro

**Restricciones:**
- `unique_together`: (`empresa`, `producto`, `almacen`, `codigo_lote`) - No puede haber dos lotes con el mismo código en la misma empresa/producto/almacén

**Métodos:**
- `esta_vencido()`: Verifica si el lote está vencido
- `dias_para_vencer()`: Retorna días restantes para vencer

#### AlertaInventario

Alertas automáticas del sistema de inventario.

**Campos:**
- `empresa` (ForeignKey): Empresa a la que pertenece la alerta (requerido)
- `inventario` (ForeignKey): Inventario relacionado (opcional)
- `lote` (ForeignKey): Lote relacionado (opcional)
- `tipo` (CharField): Tipo de alerta (STOCK_BAJO, STOCK_AGOTADO, VENCIMIENTO_PROXIMO, VENCIMIENTO_VENCIDO, STOCK_EXCESIVO)
- `prioridad` (CharField): Prioridad (BAJA, MEDIA, ALTA, CRITICA)
- `mensaje` (TextField): Mensaje de la alerta
- `fecha_alerta` (DateTimeField): Fecha de la alerta (auto_now_add)
- `fecha_resuelta` (DateTimeField): Fecha de resolución (opcional)
- `resuelta` (BooleanField): Indica si la alerta está resuelta (default: False)
- `usuario_resolucion` (ForeignKey): Usuario que resolvió la alerta (opcional)
- `uuid` (UUIDField): Identificador único universal
- `fecha_creacion` (DateTimeField): Fecha de creación (auto)
- `fecha_actualizacion` (DateTimeField): Fecha de última actualización (auto)
- `usuario_creacion` (ForeignKey): Usuario que creó el registro
- `usuario_modificacion` (ForeignKey): Usuario que modificó el registro

#### TransferenciaInventario

Transferencias de productos entre almacenes.

**Campos:**
- `empresa` (ForeignKey): Empresa a la que pertenece la transferencia (requerido)
- `almacen_origen` (ForeignKey): Almacén origen (requerido)
- `almacen_destino` (ForeignKey): Almacén destino (requerido)
- `numero_transferencia` (CharField): Número único de transferencia (requerido)
- `fecha_solicitud` (DateTimeField): Fecha de solicitud (auto_now_add)
- `fecha_envio` (DateTimeField): Fecha de envío (opcional)
- `fecha_recepcion` (DateTimeField): Fecha de recepción (opcional)
- `estado` (CharField): Estado (PENDIENTE, EN_TRANSITO, RECIBIDA_PARCIAL, RECIBIDA, CANCELADA)
- `motivo` (TextField): Motivo de la transferencia
- `usuario_solicitante` (ForeignKey): Usuario que solicitó la transferencia
- `usuario_receptor` (ForeignKey): Usuario que recibió la transferencia (opcional)
- `uuid` (UUIDField): Identificador único universal
- `idempotency_key` (CharField): Clave para operaciones idempotentes
- `fecha_creacion` (DateTimeField): Fecha de creación (auto)
- `fecha_actualizacion` (DateTimeField): Fecha de última actualización (auto)
- `usuario_creacion` (ForeignKey): Usuario que creó el registro
- `usuario_modificacion` (ForeignKey): Usuario que modificó el registro

**Restricciones:**
- `unique_together`: (`empresa`, `numero_transferencia`) - No puede haber dos transferencias con el mismo número en la misma empresa

**Relación:**
- `detalles` (DetalleTransferencia): Detalles de productos transferidos

#### DetalleTransferencia

Detalle de productos en una transferencia.

**Campos:**
- `transferencia` (ForeignKey): Transferencia padre (requerido)
- `producto` (ForeignKey): Producto transferido (requerido)
- `lote` (ForeignKey): Lote transferido (opcional)
- `cantidad_solicitada` (DecimalField): Cantidad solicitada (requerido)
- `cantidad_enviada` (DecimalField): Cantidad enviada (default: 0)
- `cantidad_recibida` (DecimalField): Cantidad recibida (default: 0)
- `costo_unitario` (DecimalField): Costo unitario
- `observaciones` (TextField): Observaciones

#### AjusteInventario

Ajustes de inventario que requieren aprobación.

**Campos:**
- `empresa` (ForeignKey): Empresa a la que pertenece el ajuste (requerido)
- `almacen` (ForeignKey): Almacén del ajuste (requerido)
- `tipo_ajuste` (CharField): Tipo de ajuste (AJUSTE_INVENTARIO, AJUSTE_DIFERENCIA, AJUSTE_DETERIORO, etc.)
- `motivo` (TextField): Motivo del ajuste (requerido)
- `fecha_ajuste` (DateField): Fecha del ajuste (requerido)
- `estado` (CharField): Estado (PENDIENTE, APROBADO, RECHAZADO, PROCESADO)
- `usuario_solicitante` (ForeignKey): Usuario que solicitó el ajuste
- `usuario_aprobador` (ForeignKey): Usuario que aprobó el ajuste (opcional)
- `fecha_aprobacion` (DateTimeField): Fecha de aprobación (opcional)
- `observaciones_aprobacion` (TextField): Observaciones de aprobación
- `uuid` (UUIDField): Identificador único universal
- `idempotency_key` (CharField): Clave para operaciones idempotentes
- `fecha_creacion` (DateTimeField): Fecha de creación (auto)
- `fecha_actualizacion` (DateTimeField): Fecha de última actualización (auto)
- `usuario_creacion` (ForeignKey): Usuario que creó el registro
- `usuario_modificacion` (ForeignKey): Usuario que modificó el registro

**Relación:**
- `detalles` (DetalleAjusteInventario): Detalles de productos ajustados

#### DetalleAjusteInventario

Detalle de productos en un ajuste.

**Campos:**
- `ajuste` (ForeignKey): Ajuste padre (requerido)
- `producto` (ForeignKey): Producto ajustado (requerido)
- `lote` (ForeignKey): Lote ajustado (opcional)
- `cantidad_anterior` (DecimalField): Cantidad anterior (requerido)
- `cantidad_nueva` (DecimalField): Cantidad nueva (requerido)
- `diferencia` (DecimalField): Diferencia calculada automáticamente (cantidad_nueva - cantidad_anterior)
- `costo_unitario` (DecimalField): Costo unitario
- `observaciones` (TextField): Observaciones

#### ConteoFisico

Conteos físicos de inventario.

**Campos:**
- `empresa` (ForeignKey): Empresa a la que pertenece el conteo (requerido)
- `almacen` (ForeignKey): Almacén del conteo (requerido)
- `numero_conteo` (CharField): Número único de conteo (requerido)
- `fecha_conteo` (DateField): Fecha del conteo (requerido)
- `fecha_inicio` (DateTimeField): Fecha de inicio del conteo (opcional)
- `fecha_fin` (DateTimeField): Fecha de fin del conteo (opcional)
- `estado` (CharField): Estado (PLANIFICADO, EN_PROCESO, FINALIZADO, AJUSTADO, CANCELADO)
- `tipo_conteo` (CharField): Tipo de conteo (COMPLETO, CICLICO, SELECTIVO)
- `usuario_responsable` (ForeignKey): Usuario responsable del conteo
- `observaciones` (TextField): Observaciones
- `uuid` (UUIDField): Identificador único universal
- `idempotency_key` (CharField): Clave para operaciones idempotentes
- `fecha_creacion` (DateTimeField): Fecha de creación (auto)
- `fecha_actualizacion` (DateTimeField): Fecha de última actualización (auto)
- `usuario_creacion` (ForeignKey): Usuario que creó el registro
- `usuario_modificacion` (ForeignKey): Usuario que modificó el registro

**Restricciones:**
- `unique_together`: (`empresa`, `numero_conteo`) - No puede haber dos conteos con el mismo número en la misma empresa

**Relación:**
- `detalles` (DetalleConteoFisico): Detalles de productos contados

#### DetalleConteoFisico

Detalle de productos en un conteo físico.

**Campos:**
- `conteo` (ForeignKey): Conteo padre (requerido)
- `producto` (ForeignKey): Producto contado (requerido)
- `lote` (ForeignKey): Lote contado (opcional)
- `cantidad_sistema` (DecimalField): Cantidad según sistema (requerido)
- `cantidad_fisica` (DecimalField): Cantidad contada físicamente (requerido)
- `diferencia` (DecimalField): Diferencia calculada automáticamente (cantidad_fisica - cantidad_sistema)
- `observaciones` (TextField): Observaciones
- `contado_por` (ForeignKey): Usuario que realizó el conteo (opcional)

### Serializers

Todos los serializers incluyen campos calculados y validaciones personalizadas:

- **AlmacenSerializer**: Validación de nombre único por empresa
- **InventarioProductoSerializer**: Validación de que producto y almacén pertenezcan a la misma empresa
- **MovimientoInventarioSerializer**: Validación de stock suficiente para salidas, cantidad positiva
- **ReservaStockSerializer**: Validación de stock disponible, cantidad positiva
- **LoteSerializer**: Validación de código de lote único por empresa, cantidad disponible no excede cantidad inicial
- **AlertaInventarioSerializer**: Validación de que al menos inventario o lote esté presente
- **TransferenciaInventarioSerializer**: Validación de número único por empresa, almacenes pertenezcan a la misma empresa
- **AjusteInventarioSerializer**: Validación de que almacén pertenezca a la empresa
- **ConteoFisicoSerializer**: Validación de número único por empresa, almacén pertenezca a la empresa

Todos los serializers incluyen `read_only_fields` con campos de auditoría y empresa.

### Viewsets (API Endpoints)

#### AlmacenViewSet

**Endpoint:** `/api/v1/almacenes/`

**Características:**
- Hereda de `IdempotencyMixin` para operaciones idempotentes
- Filtrado automático por empresa del usuario autenticado
- Búsqueda por nombre y dirección
- Ordenamiento por nombre y fecha de creación
- Filtro: `?activo=true/false`

**Métodos HTTP:**
- `GET /api/v1/almacenes/` - Listar almacenes
- `POST /api/v1/almacenes/` - Crear almacén
- `GET /api/v1/almacenes/{id}/` - Obtener almacén
- `PUT /api/v1/almacenes/{id}/` - Actualizar almacén completo
- `PATCH /api/v1/almacenes/{id}/` - Actualizar almacén parcial
- `DELETE /api/v1/almacenes/{id}/` - Eliminar almacén

#### InventarioProductoViewSet

**Endpoint:** `/api/v1/inventario/existencias/`

**Características:**
- Hereda de `IdempotencyMixin` para operaciones idempotentes
- Filtrado automático por empresa del usuario autenticado
- Búsqueda por nombre y código SKU del producto
- Ordenamiento por nombre del producto, cantidad disponible y fecha de creación
- Filtros: `?almacen={id}`, `?producto={id}`, `?bajo_minimo=true`

**Métodos HTTP:**
- `GET /api/v1/inventario/existencias/` - Listar inventarios
- `POST /api/v1/inventario/existencias/` - Crear inventario
- `GET /api/v1/inventario/existencias/{id}/` - Obtener inventario
- `PUT /api/v1/inventario/existencias/{id}/` - Actualizar inventario completo
- `PATCH /api/v1/inventario/existencias/{id}/` - Actualizar inventario parcial
- `DELETE /api/v1/inventario/existencias/{id}/` - Eliminar inventario

#### MovimientoInventarioViewSet

**Endpoint:** `/api/v1/inventario/movimientos/`

**Características:**
- Hereda de `IdempotencyMixin` para operaciones idempotentes
- Filtrado automático por empresa del usuario autenticado
- Búsqueda por nombre y código SKU del producto, referencia
- Ordenamiento por fecha y tipo de movimiento
- Filtros: `?producto={id}`, `?almacen={id}`, `?tipo_movimiento={tipo}`

**Métodos HTTP:**
- `GET /api/v1/inventario/movimientos/` - Listar movimientos
- `POST /api/v1/inventario/movimientos/` - Crear movimiento
- `GET /api/v1/inventario/movimientos/{id}/` - Obtener movimiento
- `PUT /api/v1/inventario/movimientos/{id}/` - Actualizar movimiento completo
- `PATCH /api/v1/inventario/movimientos/{id}/` - Actualizar movimiento parcial
- `DELETE /api/v1/inventario/movimientos/{id}/` - Eliminar movimiento

**Acciones Personalizadas:**
- `GET /api/v1/inventario/movimientos/kardex/?producto_id={id}&almacen_id={id}&fecha_desde={fecha}&fecha_hasta={fecha}` - Obtener kardex del producto

#### ReservaStockViewSet

**Endpoint:** `/api/v1/inventario/reservas/`

**Características:**
- Hereda de `IdempotencyMixin` para operaciones idempotentes
- Filtrado automático por empresa del usuario autenticado
- Búsqueda por referencia y nombre del producto
- Ordenamiento por fecha de reserva y estado
- Filtro: `?estado={estado}`

**Métodos HTTP:**
- `GET /api/v1/inventario/reservas/` - Listar reservas
- `POST /api/v1/inventario/reservas/` - Crear reserva
- `GET /api/v1/inventario/reservas/{id}/` - Obtener reserva
- `PUT /api/v1/inventario/reservas/{id}/` - Actualizar reserva completo
- `PATCH /api/v1/inventario/reservas/{id}/` - Actualizar reserva parcial
- `DELETE /api/v1/inventario/reservas/{id}/` - Eliminar reserva

**Acciones Personalizadas:**
- `POST /api/v1/inventario/reservas/{id}/confirmar/` - Confirmar reserva
- `POST /api/v1/inventario/reservas/{id}/cancelar/` - Cancelar reserva

#### LoteViewSet

**Endpoint:** `/api/v1/inventario/lotes/`

**Características:**
- Hereda de `IdempotencyMixin` para operaciones idempotentes
- Filtrado automático por empresa del usuario autenticado
- Búsqueda por código de lote, número de lote, nombre y código SKU del producto
- Ordenamiento por fecha de ingreso, fecha de vencimiento y estado
- Filtros: `?estado={estado}`, `?vencidos=true`, `?producto={id}`, `?almacen={id}`

**Métodos HTTP:**
- `GET /api/v1/inventario/lotes/` - Listar lotes
- `POST /api/v1/inventario/lotes/` - Crear lote
- `GET /api/v1/inventario/lotes/{id}/` - Obtener lote
- `PUT /api/v1/inventario/lotes/{id}/` - Actualizar lote completo
- `PATCH /api/v1/inventario/lotes/{id}/` - Actualizar lote parcial
- `DELETE /api/v1/inventario/lotes/{id}/` - Eliminar lote

#### AlertaInventarioViewSet

**Endpoint:** `/api/v1/inventario/alertas/`

**Características:**
- Hereda de `IdempotencyMixin` para operaciones idempotentes
- Filtrado automático por empresa del usuario autenticado
- Por defecto muestra solo alertas no resueltas
- Búsqueda por mensaje, nombre del producto y código de lote
- Ordenamiento por fecha de alerta, prioridad y tipo
- Filtros: `?resueltas=true`, `?tipo={tipo}`, `?prioridad={prioridad}`

**Métodos HTTP:**
- `GET /api/v1/inventario/alertas/` - Listar alertas
- `POST /api/v1/inventario/alertas/` - Crear alerta
- `GET /api/v1/inventario/alertas/{id}/` - Obtener alerta
- `PUT /api/v1/inventario/alertas/{id}/` - Actualizar alerta completo
- `PATCH /api/v1/inventario/alertas/{id}/` - Actualizar alerta parcial
- `DELETE /api/v1/inventario/alertas/{id}/` - Eliminar alerta

**Acciones Personalizadas:**
- `POST /api/v1/inventario/alertas/{id}/resolver/` - Resolver alerta
- `POST /api/v1/inventario/alertas/generar_alertas/` - Generar todas las alertas

#### TransferenciaInventarioViewSet

**Endpoint:** `/api/v1/inventario/transferencias/`

**Características:**
- Hereda de `IdempotencyMixin` para operaciones idempotentes
- Filtrado automático por empresa del usuario autenticado
- Búsqueda por número de transferencia y nombres de almacenes
- Ordenamiento por fecha de solicitud y estado
- Filtros: `?estado={estado}`, `?almacen_origen={id}`, `?almacen_destino={id}`

**Métodos HTTP:**
- `GET /api/v1/inventario/transferencias/` - Listar transferencias
- `POST /api/v1/inventario/transferencias/` - Crear transferencia
- `GET /api/v1/inventario/transferencias/{id}/` - Obtener transferencia
- `PUT /api/v1/inventario/transferencias/{id}/` - Actualizar transferencia completo
- `PATCH /api/v1/inventario/transferencias/{id}/` - Actualizar transferencia parcial
- `DELETE /api/v1/inventario/transferencias/{id}/` - Eliminar transferencia

**Acciones Personalizadas:**
- `POST /api/v1/inventario/transferencias/{id}/enviar/` - Marcar transferencia como enviada
- `POST /api/v1/inventario/transferencias/{id}/recibir/` - Marcar transferencia como recibida

#### AjusteInventarioViewSet

**Endpoint:** `/api/v1/inventario/ajustes/`

**Características:**
- Hereda de `IdempotencyMixin` para operaciones idempotentes
- Filtrado automático por empresa del usuario autenticado
- Búsqueda por motivo y nombre del almacén
- Ordenamiento por fecha de ajuste y estado
- Filtros: `?estado={estado}`, `?tipo_ajuste={tipo}`, `?almacen={id}`

**Métodos HTTP:**
- `GET /api/v1/inventario/ajustes/` - Listar ajustes
- `POST /api/v1/inventario/ajustes/` - Crear ajuste
- `GET /api/v1/inventario/ajustes/{id}/` - Obtener ajuste
- `PUT /api/v1/inventario/ajustes/{id}/` - Actualizar ajuste completo
- `PATCH /api/v1/inventario/ajustes/{id}/` - Actualizar ajuste parcial
- `DELETE /api/v1/inventario/ajustes/{id}/` - Eliminar ajuste

**Acciones Personalizadas:**
- `POST /api/v1/inventario/ajustes/{id}/aprobar/` - Aprobar ajuste
- `POST /api/v1/inventario/ajustes/{id}/rechazar/` - Rechazar ajuste
- `POST /api/v1/inventario/ajustes/{id}/procesar/` - Procesar ajuste aprobado (aplica cambios al inventario)

#### ConteoFisicoViewSet

**Endpoint:** `/api/v1/inventario/conteos-fisicos/`

**Características:**
- Hereda de `IdempotencyMixin` para operaciones idempotentes
- Filtrado automático por empresa del usuario autenticado
- Búsqueda por número de conteo y nombre del almacén
- Ordenamiento por fecha de conteo y estado
- Filtros: `?estado={estado}`, `?tipo_conteo={tipo}`, `?almacen={id}`

**Métodos HTTP:**
- `GET /api/v1/inventario/conteos-fisicos/` - Listar conteos
- `POST /api/v1/inventario/conteos-fisicos/` - Crear conteo
- `GET /api/v1/inventario/conteos-fisicos/{id}/` - Obtener conteo
- `PUT /api/v1/inventario/conteos-fisicos/{id}/` - Actualizar conteo completo
- `PATCH /api/v1/inventario/conteos-fisicos/{id}/` - Actualizar conteo parcial
- `DELETE /api/v1/inventario/conteos-fisicos/{id}/` - Eliminar conteo

**Acciones Personalizadas:**
- `POST /api/v1/inventario/conteos-fisicos/{id}/iniciar/` - Iniciar conteo
- `POST /api/v1/inventario/conteos-fisicos/{id}/finalizar/` - Finalizar conteo
- `POST /api/v1/inventario/conteos-fisicos/{id}/ajustar/` - Ajustar inventario basado en diferencias del conteo

### Admin de Django

Todos los modelos están registrados en el admin de Django con configuraciones personalizadas:

- **AlmacenAdmin**: list_display, list_filter, search_fields, fieldsets
- **InventarioProductoAdmin**: list_display, list_filter, search_fields, fieldsets
- **MovimientoInventarioAdmin**: list_display, list_filter, search_fields, fieldsets
- **ReservaStockAdmin**: list_display, list_filter, search_fields, fieldsets
- **LoteAdmin**: list_display, list_filter, search_fields, fieldsets
- **AlertaInventarioAdmin**: list_display, list_filter, search_fields, fieldsets
- **TransferenciaInventarioAdmin**: list_display, list_filter, search_fields, fieldsets con inline para detalles
- **AjusteInventarioAdmin**: list_display, list_filter, search_fields, fieldsets con inline para detalles
- **ConteoFisicoAdmin**: list_display, list_filter, search_fields, fieldsets con inline para detalles

## Características Principales

### Multi-empresa
- Todos los registros están asociados a una empresa
- El filtrado automático asegura que los usuarios solo vean datos de su empresa
- Las restricciones de unicidad son por empresa

### Auditoría
- Registro automático de usuario y fecha de creación
- Registro automático de usuario y fecha de modificación
- Campos UUID para identificación única
- Trazabilidad completa de movimientos

### Idempotencia
- Soporte para operaciones idempotentes mediante `idempotency_key`
- Previene duplicación de registros en operaciones repetidas

### Control de Stock
- Validación de stock suficiente antes de salidas
- Reservas de stock para cotizaciones y facturas pendientes
- Cálculo automático de stock disponible real (disponible - reservas)
- Alertas automáticas para stock bajo mínimo y agotado

### Gestión de Lotes
- Control de fechas de fabricación y vencimiento
- Alertas automáticas para lotes próximos a vencer y vencidos
- Trazabilidad completa por lote

### Transferencias entre Almacenes
- Flujo completo de transferencias (solicitud → envío → recepción)
- Validación de que ambos almacenes pertenezcan a la misma empresa
- Registro automático de movimientos de entrada y salida

### Ajustes de Inventario
- Sistema de aprobación para ajustes
- Diferentes tipos de ajustes (diferencia, deterioro, robo, donación, etc.)
- Procesamiento automático que aplica cambios al inventario

### Conteos Físicos
- Diferentes tipos de conteo (completo, cíclico, selectivo)
- Cálculo automático de diferencias
- Ajuste automático del inventario basado en diferencias

### Métodos de Valoración
- Costo Promedio Ponderado (PROMEDIO)
- Primero en Entrar, Primero en Salir (PEPS/FIFO)
- Último en Entrar, Primero en Salir (UEPS/LIFO)
- Precio Específico

### Servicios

#### ServicioInventario

Métodos principales:
- `puede_realizar_movimiento()`: Valida si se puede realizar un movimiento
- `registrar_movimiento()`: Registra un movimiento y actualiza el inventario
- `crear_reserva()`: Crea una reserva de stock
- `confirmar_reserva()`: Confirma una reserva
- `cancelar_reserva()`: Cancela una reserva

#### ServicioAlertasInventario

Métodos principales:
- `verificar_stock_bajo()`: Genera alertas para productos bajo mínimo
- `verificar_vencimientos()`: Genera alertas para lotes próximos a vencer
- `verificar_stock_excesivo()`: Genera alertas para productos con stock excesivo
- `generar_todas_las_alertas()`: Genera todas las alertas del sistema

## Ejemplos de Uso

### Crear un Almacén

```http
POST /api/v1/almacenes/
Content-Type: application/json
Authorization: Bearer {token}

{
  "nombre": "Almacén Principal",
  "descripcion": "Almacén principal de la empresa",
  "direccion": "Calle Principal #123",
  "activo": true
}
```

### Obtener Kardex de un Producto

```http
GET /api/v1/inventario/movimientos/kardex/?producto_id=1&almacen_id=1&fecha_desde=2024-01-01&fecha_hasta=2024-01-31
Authorization: Bearer {token}
```

**Respuesta:**
```json
{
  "producto": {
    "id": 1,
    "nombre": "Producto ABC",
    "codigo_sku": "ABC-001"
  },
  "almacen": {
    "id": 1,
    "nombre": "Almacén Principal"
  },
  "fecha_desde": "2024-01-01",
  "fecha_hasta": "2024-01-31",
  "saldo_inicial": 100.00,
  "saldo_final": 150.00,
  "total_movimientos": 5,
  "movimientos": [
    {
      "id": 1,
      "fecha": "2024-01-05T10:00:00Z",
      "tipo_movimiento": "ENTRADA_COMPRA",
      "cantidad": 50.00,
      "costo_unitario": 10.00,
      "valor_total": 500.00,
      "saldo_acumulado": 150.00,
      "referencia": "COMPRA-001",
      "usuario": "admin"
    }
  ]
}
```

### Crear una Reserva de Stock

```http
POST /api/v1/inventario/reservas/
Content-Type: application/json
Authorization: Bearer {token}

{
  "inventario": 1,
  "cantidad_reservada": 10.00,
  "referencia": "COT-001",
  "fecha_vencimiento": "2024-12-31T23:59:59Z"
}
```

### Crear una Transferencia entre Almacenes

```http
POST /api/v1/inventario/transferencias/
Content-Type: application/json
Authorization: Bearer {token}

{
  "almacen_origen": 1,
  "almacen_destino": 2,
  "numero_transferencia": "TRF-001",
  "motivo": "Reabastecimiento de almacén secundario",
  "detalles": [
    {
      "producto": 1,
      "cantidad_solicitada": 20.00,
      "costo_unitario": 10.00
    }
  ]
}
```

### Crear un Ajuste de Inventario

```http
POST /api/v1/inventario/ajustes/
Content-Type: application/json
Authorization: Bearer {token}

{
  "almacen": 1,
  "tipo_ajuste": "AJUSTE_DIFERENCIA",
  "motivo": "Diferencia encontrada en conteo físico",
  "fecha_ajuste": "2024-01-15",
  "detalles": [
    {
      "producto": 1,
      "cantidad_anterior": 100.00,
      "cantidad_nueva": 95.00,
      "costo_unitario": 10.00
    }
  ]
}
```

### Crear un Conteo Físico

```http
POST /api/v1/inventario/conteos-fisicos/
Content-Type: application/json
Authorization: Bearer {token}

{
  "almacen": 1,
  "numero_conteo": "CONT-001",
  "fecha_conteo": "2024-01-15",
  "tipo_conteo": "COMPLETO",
  "detalles": [
    {
      "producto": 1,
      "cantidad_sistema": 100.00,
      "cantidad_fisica": 95.00
    }
  ]
}
```

## Flujos de Trabajo

### Flujo de Transferencia entre Almacenes

1. **Crear transferencia**: `POST /api/v1/inventario/transferencias/` con detalles de productos
2. **Enviar transferencia**: `POST /api/v1/inventario/transferencias/{id}/enviar/` - Registra movimientos de salida
3. **Recibir transferencia**: `POST /api/v1/inventario/transferencias/{id}/recibir/` - Registra movimientos de entrada

### Flujo de Ajuste de Inventario

1. **Crear ajuste**: `POST /api/v1/inventario/ajustes/` con detalles de productos
2. **Aprobar ajuste**: `POST /api/v1/inventario/ajustes/{id}/aprobar/` - Requiere permisos de aprobación
3. **Procesar ajuste**: `POST /api/v1/inventario/ajustes/{id}/procesar/` - Aplica cambios al inventario

### Flujo de Conteo Físico

1. **Crear conteo**: `POST /api/v1/inventario/conteos-fisicos/` con detalles de productos
2. **Iniciar conteo**: `POST /api/v1/inventario/conteos-fisicos/{id}/iniciar/` - Cambia estado a EN_PROCESO
3. **Finalizar conteo**: `POST /api/v1/inventario/conteos-fisicos/{id}/finalizar/` - Cambia estado a FINALIZADO
4. **Ajustar inventario**: `POST /api/v1/inventario/conteos-fisicos/{id}/ajustar/` - Crea ajuste automático y aplica diferencias

## Notas de Implementación

### Cambios Recientes

1. **Campo `empresa` agregado**: Todos los modelos principales ahora incluyen el campo `empresa` como ForeignKey requerido
2. **Campos de auditoría agregados**: `usuario_creacion` y `usuario_modificacion` en todos los modelos principales
3. **Restricciones `unique_together` actualizadas**: Ahora incluyen `empresa` para permitir nombres/números duplicados entre diferentes empresas
4. **Filtrado multi-empresa corregido**: Todos los ViewSets ahora usan `self.request.user.empresa` en lugar de `getattr`
5. **IdempotencyMixin agregado**: `InventarioProductoViewSet` y `AlertaInventarioViewSet` ahora soportan operaciones idempotentes
6. **Validaciones mejoradas**: Todos los serializers incluyen validaciones personalizadas
7. **Admin configurado**: Todos los modelos están registrados en el admin de Django con configuración personalizada

### Dependencias

- `empresas.Empresa`: Modelo de empresa (requerido)
- `productos.Producto`: Modelo de producto (requerido)
- `proveedores.Proveedor`: Modelo de proveedor (opcional, para lotes)
- `compras.Compra`: Modelo de compra (opcional, para lotes)
- `usuarios.User`: Modelo de usuario (requerido para auditoría)

### Permisos

El módulo utiliza `ActionBasedPermission` que requiere:
- Autenticación del usuario
- Permisos específicos según la acción (crear, leer, actualizar, eliminar)

### Consideraciones de Rendimiento

- Los movimientos de inventario se registran con `select_for_update()` para evitar condiciones de carrera
- Las consultas usan `select_related()` y `prefetch_related()` para optimizar el rendimiento
- Los índices en la base de datos optimizan las consultas frecuentes

## Próximas Mejoras Sugeridas

1. Implementar cálculo de rotación de inventario más preciso
2. Agregar reportes de inventario (valorización, rotación, etc.)
3. Implementar notificaciones automáticas para alertas críticas
4. Agregar validación de fechas de vencimiento antes de crear facturas
5. Implementar sistema de reordenamiento automático
6. Agregar historial de cambios de costos
7. Implementar exportación de kardex a Excel/PDF
8. Agregar dashboard de inventario con métricas clave

