# Especificaciones del Proyecto: Sistema de Facturación Django + Next.js

## Objetivo general 

Se tienen que cumplir esos principcios nunca lo olvides DRY · KISS · SRP · SoC · YAGNI

Construir un **sistema de facturación para República Dominicana** que incluya: 

- **Soporte Multiempresa**: Gestión de múltiples empresas en una misma instalación (Multi-tenant).
- Catálogo de **clientes** 
- Catálogo de **productos y servicios** + **categorías** 
- Catálogo de **proveedores** 
- **Proceso de compras**: 
  - Solicitud de cotizaciones a proveedores 
  - Órdenes de compra a proveedores 
  - Registro de compras 
- **Proceso de ventas**: 
  - Cotizaciones al cliente 
  - Conversión de cotización en venta/factura 
  - Pago en caja (contado / crédito / pagos parciales) 
- **Devoluciones** (cliente y proveedor) 
- **Notas de crédito** 
- **Notas de débito** 
- **Historial de compra por proveedor y por producto** 
- **Kardex de inventario** 
- **Movimientos de inventario** 
- **Módulo de despachos** (salida de productos desde almacén) 
- **Seguridad granular** por rol/permiso y validaciones avanzadas 
- Alta **integridad de datos** + **idempotencia** en todas las operaciones críticas 

Todo con un **backend en Django + Django REST Framework** usando **PostgreSQL**, y un **frontend moderno fluido con Next.js**. 

--- 

## Stack tecnológico 

### Backend 

- Lenguaje: **Python 3.12+** 
- Framework: **Django** (versión estable más reciente) 
- API: **Django REST Framework (DRF)** 
- Base de datos: **PostgreSQL** 
- ORM: Django ORM 
- Migraciones: migraciones estándar de Django 

### Frontend 

- Framework: **Next.js** (versión actual, App Router) 
- Lenguaje: **TypeScript** 
- Estilos: **Tailwind CSS** 
- UI: 
  - Diseño limpio, moderno, responsivo (desktop + móvil) 
  - Componentes reutilizables para tablas, formularios, modales 
  - Manejo de estado en el frontend (puede ser React Query / Zustand / Context, elige una opción estándar y documenta) 

--- 

## Reglas generales de diseño 

1. **Nombres en español**  
   - Entidades, campos, clases, métodos y mensajes de error en español. 
   - Ejemplo: `Cliente`, `Proveedor`, `Producto`, `Categoria`, `Factura`, etc. 

2. **Buenas prácticas Django/DRF**  
   - Usar `settings.py` bien organizado (separar configuración de base de datos, CORS, DRF, etc.). 
   - Usar `ViewSets` o vistas API de DRF con `routers` para los módulos CRUD. 
   - Serializers separados por entidad (`ClienteSerializer`, `ProductoSerializer`, etc.). 
   - Validaciones en: 
     - `validators` y `clean()` cuando aplique. 
     - `serializers` para reglas de negocio. 
   - Respuestas JSON consistentes (estructura estándar para éxito y error). 

3. **Buenas prácticas Next.js**  
   - App Router. 
   - Rutas anidadas para cada módulo:  
     - `/clientes`, `/productos`, `/servicios`, `/categorias`, `/proveedores`, `/compras`, `/ventas`, `/caja`, `/inventario`, `/despachos`, etc. 
   - Formularios con validaciones en cliente (por ejemplo con React Hook Form + Zod o similar). 
   - Manejo de errores de API elegante (toasts / mensajes visibles). 
   - Uso de componentes reutilizables (tablas, filtros, formularios, botones, layouts). 

--- 

## Modelo de datos (mínimo requerido) 

### Configuración Multiempresa

Entidad `Empresa`:
- `id`
- `nombre`
- `rnc`
- `direccion`
- `telefono`
- `logo`
- `configuracion_fiscal` (secuencias de NCF, etc.)
- `activo`

**Nota importante**: Todas las entidades principales (Clientes, Proveedores, Productos, Facturas, Compras, Inventario, etc.) deben tener una relación (`ForeignKey`) con la entidad `Empresa`. El sistema debe filtrar automáticamente la información para que cada usuario vea solo los datos de su empresa asignada.

### Catálogo de clientes 

Entidad `Cliente`: 
- `id` 
- `nombre` (requerido) 
- `tipo_identificacion` (RNC, Cédula, Pasaporte, Otro) 
- `numero_identificacion` (único cuando aplique) 
- `telefono` 
- `correo_electronico` 
- `direccion` 
- `limite_credito` 
- `activo` (bool) 
- `fecha_creacion` 
- `fecha_actualizacion` 

Validaciones: 
- Identificación requerida para clientes a crédito. 
- Formato de correo válido. 
- Límite de crédito no negativo. 

### Historial y Reportes de Cliente

El sistema debe permitir consultar el historial completo de un cliente:
- Compras realizadas (Facturas)
- Cotizaciones solicitadas
- Pagos realizados
- Saldo pendiente (CxC)
- Productos más comprados

### Catálogo de proveedores 

Entidad `Proveedor`: 
- `id` 
- `nombre` 
- `tipo_identificacion` (RNC, Cédula, Pasaporte, Otro) 
- `numero_identificacion` 
- `telefono` 
- `correo_electronico` 
- `direccion` 
- `es_internacional` (bool) 
- `activo` 
- `fecha_creacion` 
- `fecha_actualizacion` 

### Productos, servicios y categorías 

Entidad `Categoria`: 
- `id` 
- `nombre` 
- `descripcion` 
- `activa` 

Entidad `Producto`: 
- `id` 
- `codigo_sku` (SKU / Código de barras) 
- `codigo_interno` (Generado automáticamente por el sistema)
- `nombre` 
- `nombre_local` (Nombre comercial o variante local)
- `descripcion` 
- `es_servicio` (bool) 
- `referencias_cruzadas` (Lista de códigos equivalentes o sustitutos)
- `precio_venta_base` 
- `lleva_itbis` (bool) - Indica si el producto grava impuestos
- `impuesto_itbis` (porcentaje aplicado si `lleva_itbis` es true) 
- `fotos` (Galería de imágenes)
- Relación con categorías (muchos a muchos) 
- `activo` 
- `fecha_creacion` 
- `fecha_actualizacion` 

### Compras 

Flujo: 
1. **Solicitud de cotización a proveedor**  
   Entidad `SolicitudCotizacionProveedor`: 
   - Proveedor 
   - Fecha 
   - Estado (Pendiente, Recibida, Cancelada) 
   - Detalles solicitados (productos/servicios, cantidades) 

2. **Órdenes de compra**  
   Entidad `OrdenCompra`: 
   - Proveedor 
   - Fecha 
   - Estado (Borrador, Aprobada, EnRecepcion, Recibida, Cancelada) 
   - Moneda 
   - Condiciones de pago 
   - Detalles (producto, cantidad, costo unitario, impuestos, descuentos) 

3. **Recepción de Mercancía**  
   Entidad `RecepcionCompra`:
   - Referencia a `OrdenCompra`
   - Fecha de recepción
   - Almacén de destino
   - Detalles recibidos (producto, cantidad recibida, lotes)
   - Debe actualizar el inventario (entrada de stock).
   - Debe actualizar el estado de la Orden de Compra (Recibida Parcial / Recibida Total).

4. **Liquidación de Importaciones (Compras Internacionales)**
   - Si el proveedor es internacional (`es_internacional=True`).
   - Entidad `LiquidacionImportacion`:
     - Referencia a `OrdenCompra` o `Compra`
     - Incoterm (FOB, CIF, EXW, etc.)
     - Tasa de cambio aplicada
     - Lista de **Gastos Adicionales** (Flete, Seguro, Aduanas, Transporte local)
   - **Distribución de Costos**:
     - Funcionalidad para prorratear los gastos adicionales entre los productos recibidos (por valor FOB o por peso/volumen).
     - Actualización del **Costo Unitario Real** en el inventario (Costo FOB + Gastos prorrateados).

5. **Registro de compra / facturas de proveedor**  
   Entidad `Compra`: 
   - Referencia a `OrdenCompra` o `RecepcionCompra`
   - Proveedor 
   - Fecha 
   - Número de factura del proveedor 
   - Estado (Registrada, Pagada, ParcialmentePagada) 
   - Totales: subtotal, impuestos, descuentos, total 
   - Detalles por producto/lote 

### Cuentas por Pagar (CxP)

Entidad `CuentaPorPagar`:
- Relación con `Proveedor`
- Relación con `Compra` (origen de la deuda)
- Fecha de emisión
- Fecha de vencimiento
- Monto original
- Monto pendiente
- Estado (Pendiente, Pagada Parcial, Pagada, Vencida)

Entidad `PagoProveedor`:
- Relación con `Proveedor`
- Fecha de pago
- Monto pagado
- Método de pago (Cheque, Transferencia, Efectivo)
- Referencia (Número de cheque o transferencia)
- Cuenta bancaria origen (opcional, si se manejan bancos)
- Usuario que registra
- **Distribución del pago**: Un solo pago puede abonar a múltiples facturas/cuentas por pagar.

### Ventas y facturación 

Flujo: 
1. **Cotización al cliente** (`CotizacionCliente`) 
   - Cliente 
   - Fecha 
   - Vigencia 
   - Estado (Pendiente, Aprobada, Rechazada, Expirada) 
   - Detalles (productos/servicios, cantidades, precios, descuentos) 
   - No permitir cotización vacía. 

2. **Factura / Venta** (`Factura`) 
   - Cliente 
   - Fecha 
   - Número de factura (Interno)
   - **NCF** (Número de Comprobante Fiscal): **Solo se genera al confirmar el pago o finalizar la venta a crédito**, para evitar huecos en la secuencia fiscal por cancelaciones.
   - Estado (Borrador, PendientePago, PagadaParcial, Pagada, Cancelada) 
   - Referencia a cotización (si viene de cotización) 
   - Totales: subtotal, ITBIS, descuentos, total, monto_pendiente 
   - Tipo de venta: Contado / Crédito 

3. **Pago en caja** (`PagoCaja`) 
   - Referencia a una o varias facturas 
   - Cliente 
   - Fecha/hora 
   - Monto pagado 
   - Método de pago (efectivo, tarjeta, transferencia, etc.) 
   - Usuario que registra el pago 
   - Permitir pagos parciales a una factura y pagos que cubran varias facturas. 
   - Actualizar el monto pendiente de las facturas de forma transaccional. 

### Cuentas por Cobrar (CxC)

Entidad `CuentaPorCobrar`:
- Relación con `Cliente`
- Relación con `Factura` (origen de la deuda)
- Fecha de emisión
- Fecha de vencimiento
- Monto original
- Monto pendiente
- Estado (Pendiente, Pagada Parcial, Pagada, Vencida, Incobrable)

Entidad `CobroCliente` (Recibo de Ingreso):
- Relación con `Cliente`
- Fecha de cobro
- Monto total cobrado
- Método de pago (Efectivo, Tarjeta, Cheque, Transferencia)
- Referencia (No. Cheque, Voucher, Transacción)
- Caja / Banco destino
- Usuario que registra
- **Distribución del cobro**: Un solo cobro puede abonar a múltiples facturas/cuentas por cobrar.

### Devoluciones, notas de crédito y débito 

- **Devolución de venta**: 
  - Entidad `DevolucionVenta`: 
    - Factura asociada 
    - Cliente 
    - Fecha 
    - Motivo (defecto, error, comercial, etc.) 
    - Detalles (productos, cantidades devueltas) 
    - Integración con inventario (devuelve productos al inventario según tipo de devolución). 
- **Nota de crédito**: 
  - Entidad `NotaCredito`: 
    - Referencia a factura (cuando aplique) 
    - Cliente 
    - Monto 
    - Motivo 
    - Aplicación al saldo del cliente. 
- **Nota de débito**: 
  - Entidad `NotaDebito`: 
    - Referencia a factura (cuando aplique) 
    - Cliente 
    - Monto 
    - Motivo 

### Caja y Turnos

Entidad `Caja`:
- `id`
- `nombre` (Ej. Caja Principal, Caja 2)
- `activa` (bool)

Entidad `TurnoCaja`:
- `id`
- `caja`
- `usuario_apertura`
- `usuario_cierre`
- `fecha_apertura`
- `fecha_cierre`
- `monto_apertura` (Fondo de caja)
- `monto_cierre_sistema` (Calculado: Apertura + Ingresos - Egresos)
- `monto_cierre_real` (Lo que cuenta el cajero)
- `diferencia` (Sobante / Faltante)
- `estado` (Abierta, Cerrada, Arqueada)

Entidad `MovimientoCaja`:
- `turno`
- `tipo` (IngresoVenta, IngresoCxC, EgresoGasto, RetiroEfectivo, etc.)
- `monto`
- `concepto`
- `referencia_documento`
- `usuario`

### Inventario, movimientos, kardex y despachos 

Entidad `Almacen`: 
- `id` 
- `nombre` 
- `descripcion` 
- `direccion` 
- `activo` 

Entidad `InventarioProducto` o por lotes: 
- Producto 
- Almacén 
- Cantidad disponible 
- Costo promedio o manejo por lote 

Entidad `MovimientoInventario`: 
- `id` 
- Producto (o lote) 
- Almacén origen/destino 
- Tipo de movimiento (EntradaCompra, SalidaVenta, Transferencia, AjustePositivo, AjusteNegativo, DevolucionCliente, DevolucionProveedor, etc.) 
- Cantidad 
- Fecha/hora 
- Referencia a documento origen (Compra, Factura, Devolución, Ajuste, etc.) 
- Usuario que realiza el movimiento 

**Kardex**: 
- Implementar una consulta (endpoint en la API) que devuelva el historial de movimientos por producto y almacén, con saldo acumulado. 

**Despachos** (`Despacho`): 
- Relacionar con `Factura` o `Pedido`: 
  - Cliente, Fecha, Almacén, Estado (Pendiente, Parcial, Completado). 
  - Detalles de productos y cantidades despachadas. 
- Ligado a `MovimientoInventario` para registrar la salida. 

--- 

## Auditoría y Trazabilidad

**Requisito Obligatorio**:
- **Registro de Usuario**: Cada entidad transaccional y de catálogo debe registrar qué usuario creó el registro y, si aplica, quién lo modificó por última vez.
- **Campos estándar**:
  - `id` (Identificador único interno, autoincremental o UUID)
  - `uuid` (Identificador único universal para referencia externa/API, obligatorio en documentos)
  - `usuario_creacion` (ForeignKey a Usuario)
  - `usuario_modificacion` (ForeignKey a Usuario, opcional/nulo al crear)
  - `fecha_creacion` (DateTime)
  - `fecha_modificacion` (DateTime)

## Seguridad, permisos y autenticación 

- Autenticación con tokens (JWT o similar) para la API REST. 
- Relación `Usuario` - `Empresa`:
  - Un usuario puede pertenecer a una o más empresas.
  - Al hacer login, se debe seleccionar o identificar la empresa activa en el token/sesión.
- Modelo `Usuario` + `Rol` + `Permiso`: 
  - Roles: Administrador, Facturador, Cajero, Almacén, Compras, Contabilidad, etc. 
  - Permisos por módulo y acción: 
    - Ejemplo: 
      - `clientes.ver`, `clientes.crear`, `clientes.editar`, `clientes.eliminar` 
      - `facturas.crear`, `facturas.anular`, `facturas.ver` 
      - `inventario.ver_kardex`, `inventario.ajustar`, etc. 
- En el backend: 
  - Decoradores / permisos de DRF que validen el rol/permiso antes de ejecutar la vista. 
- En el frontend: 
  - Mostrar/ocultar opciones del menú y acciones según los permisos del usuario. 

--- 

## Integridad de datos e idempotencia 

Quiero especial cuidado en: 

1. **Transacciones**: 
   - Operaciones críticas (crear factura, registrar pago, registrar compra, registrar movimientos de inventario, despachos, devoluciones) deben ejecutarse dentro de transacciones atómicas de base de datos. 
   - Si algo falla, se revierte todo. 

2. **Restricciones y claves foráneas**: 
   - Usar `ForeignKey` con `on_delete` apropiado (generalmente `PROTECT` o `RESTRICT` para no romper historial). 
   - Validar que no se eliminen entidades que tienen movimientos históricos (por ejemplo, productos con movimientos de inventario). 

3. **Idempotencia**: 
   - Para operaciones como: 
     - Creación de facturas 
     - Registro de pago en caja 
     - Creación de notas de crédito/débito 
   - Implementar un mecanismo de **idempotency key**, por ejemplo: 
     - Campo `idempotency_key` en las tablas o un modelo específico, para que si la misma petición se envía dos veces, no se duplique la operación. 
   - Ejemplo: 
     - Para `PagoCaja`, si se recibe el mismo `idempotency_key`, devolver el mismo resultado sin crear otro pago. 

4. **Control de concurrencia**: 
   - Evitar que dos operaciones simultáneas de venta se lleven la misma existencia de inventario sin verificar stock. 
   - Utilizar bloqueos adecuados o `select_for_update` cuando sea necesario. 

--- 

## Frontend (Next.js) – UX requerida 

- Dashboard inicial con: 
  - Resumen de: 
    - Ventas del día 
    - Cobros del día 
    - Deudas pendientes 
    - Alertas de stock bajo 
- Módulos con pantallas: 
  - Clientes 
   - Proveedores 
  - Productos/Servicios 
  - Categorías 
  - Compras (solicitudes de cotización, órdenes de compra, compras) 
  - Ventas (cotizaciones, facturas) 
  - Caja (registro de pagos, histórico de movimientos) 
  - Inventario (existencias, movimientos, kardex) 
  - Despachos 
- Tablas con: 
  - Búsqueda 
  - Filtros (por fecha, cliente, proveedor, estado) 
  - Paginación 
- Formularios con validación inmediata en el cliente y mensajes claros. 
- Confirmaciones antes de acciones críticas (ej. anular una factura, registrar un ajuste de inventario). 

--- 

## Entregables que espero del proyecto 

1. Proyecto completo **Django + DRF** configurado para PostgreSQL. 
2. Proyecto completo **Next.js + TypeScript + Tailwind** consumiendo la API. 
3. Scripts o instrucciones claras para: 
   - Ejecutar migraciones 
   - Crear un usuario administrador 
   - Levantar backend y frontend en entorno de desarrollo 
4. Código limpio, organizado por módulos, siguiendo las mejores prácticas de Django y Next.js. 
