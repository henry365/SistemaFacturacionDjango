# API Endpoints del Módulo de Inventario

## Base URL
`/api/v1/`

## Autenticación
Todos los endpoints requieren autenticación JWT. Incluir el token en el header:
```
Authorization: Bearer <token>
```

---

## 1. Almacenes

### Listar almacenes
```
GET /api/v1/almacenes/
```

### Crear almacén
```
POST /api/v1/almacenes/
Body: {
  "empresa": 1,
  "nombre": "Almacén Principal",
  "descripcion": "Descripción",
  "direccion": "Dirección",
  "activo": true
}
```

### Detalle de almacén
```
GET /api/v1/almacenes/{id}/
```

### Actualizar almacén
```
PUT /api/v1/almacenes/{id}/
PATCH /api/v1/almacenes/{id}/
```

### Eliminar almacén
```
DELETE /api/v1/almacenes/{id}/
```

---

## 2. Existencias (InventarioProducto)

### Listar existencias
```
GET /api/v1/inventario/existencias/
Query params:
  - search: Búsqueda por nombre o SKU del producto
```

### Detalle de existencia
```
GET /api/v1/inventario/existencias/{id}/
```

### Actualizar existencia
```
PUT /api/v1/inventario/existencias/{id}/
PATCH /api/v1/inventario/existencias/{id}/
```

---

## 3. Movimientos de Inventario

### Listar movimientos
```
GET /api/v1/inventario/movimientos/
Query params:
  - ordering: Ordenar por fecha (ej: ?ordering=-fecha)
```

### Crear movimiento
```
POST /api/v1/inventario/movimientos/
Body: {
  "empresa": 1,
  "producto": 1,
  "almacen": 1,
  "tipo_movimiento": "ENTRADA_COMPRA",
  "cantidad": 100.00,
  "costo_unitario": 50.00,
  "referencia": "COMP-001",
  "usuario": 1
}
```

### Detalle de movimiento
```
GET /api/v1/inventario/movimientos/{id}/
```

### Actualizar movimiento
```
PUT /api/v1/inventario/movimientos/{id}/
PATCH /api/v1/inventario/movimientos/{id}/
```

### Eliminar movimiento
```
DELETE /api/v1/inventario/movimientos/{id}/
```

### Kardex (Historial con saldo acumulado)
```
GET /api/v1/inventario/movimientos/kardex/?producto_id=1&almacen_id=1&fecha_desde=2024-01-01&fecha_hasta=2024-12-31
```

**Parámetros requeridos:**
- `producto_id`: ID del producto
- `almacen_id`: ID del almacén

**Parámetros opcionales:**
- `fecha_desde`: Fecha inicial (YYYY-MM-DD)
- `fecha_hasta`: Fecha final (YYYY-MM-DD)

**Respuesta:**
```json
{
  "producto": {
    "id": 1,
    "nombre": "Producto Ejemplo",
    "codigo_sku": "SKU-001"
  },
  "almacen": {
    "id": 1,
    "nombre": "Almacén Principal"
  },
  "fecha_desde": "2024-01-01",
  "fecha_hasta": "2024-12-31",
  "saldo_inicial": 100.0,
  "saldo_final": 150.0,
  "total_movimientos": 5,
  "movimientos": [...]
}
```

---

## 4. Reservas de Stock

### Listar reservas
```
GET /api/v1/inventario/reservas/
Query params:
  - search: Búsqueda por referencia o nombre de producto
  - ordering: Ordenar por fecha_reserva o estado
```

### Crear reserva
```
POST /api/v1/inventario/reservas/
Body: {
  "inventario": 1,
  "cantidad_reservada": 50.00,
  "referencia": "COT-123",
  "fecha_vencimiento": "2024-12-31T23:59:59Z",
  "usuario": 1,
  "notas": "Reserva para cotización"
}
```

### Confirmar reserva
```
POST /api/v1/inventario/reservas/{id}/confirmar/
```

### Cancelar reserva
```
POST /api/v1/inventario/reservas/{id}/cancelar/
```

---

## 5. Lotes

### Listar lotes
```
GET /api/v1/inventario/lotes/
Query params:
  - search: Búsqueda por código de lote, número de lote, nombre de producto
  - estado: Filtrar por estado (DISPONIBLE, BLOQUEADO, VENCIDO, AGOTADO)
  - vencidos: Filtrar lotes vencidos (?vencidos=true)
  - ordering: Ordenar por fecha_ingreso, fecha_vencimiento, estado
```

### Crear lote
```
POST /api/v1/inventario/lotes/
Body: {
  "empresa": 1,
  "producto": 1,
  "almacen": 1,
  "codigo_lote": "LOT-2024-001",
  "numero_lote": "12345",
  "fecha_fabricacion": "2024-01-01",
  "fecha_vencimiento": "2025-12-31",
  "cantidad_inicial": 100.00,
  "cantidad_disponible": 100.00,
  "costo_unitario": 50.00,
  "proveedor": 1,
  "compra": 1
}
```

### Detalle de lote
```
GET /api/v1/inventario/lotes/{id}/
```

### Actualizar lote
```
PUT /api/v1/inventario/lotes/{id}/
PATCH /api/v1/inventario/lotes/{id}/
```

---

## 6. Alertas de Inventario

### Listar alertas
```
GET /api/v1/inventario/alertas/
Query params:
  - resueltas: Filtrar alertas resueltas (?resueltas=true, por defecto solo no resueltas)
  - tipo: Filtrar por tipo (STOCK_BAJO, STOCK_AGOTADO, VENCIMIENTO_PROXIMO, etc.)
  - prioridad: Filtrar por prioridad (BAJA, MEDIA, ALTA, CRITICA)
  - search: Búsqueda por mensaje
  - ordering: Ordenar por fecha_alerta, prioridad, tipo
```

### Crear alerta manualmente
```
POST /api/v1/inventario/alertas/
Body: {
  "empresa": 1,
  "inventario": 1,
  "tipo": "STOCK_BAJO",
  "prioridad": "ALTA",
  "mensaje": "Stock bajo mínimo"
}
```

### Resolver alerta
```
POST /api/v1/inventario/alertas/{id}/resolver/
```

### Generar todas las alertas
```
POST /api/v1/inventario/alertas/generar_alertas/
```
Genera automáticamente todas las alertas (stock bajo, vencimientos, etc.)

---

## 7. Transferencias entre Almacenes

### Listar transferencias
```
GET /api/v1/inventario/transferencias/
Query params:
  - estado: Filtrar por estado (PENDIENTE, EN_TRANSITO, RECIBIDA, etc.)
  - search: Búsqueda por número de transferencia o nombres de almacenes
  - ordering: Ordenar por fecha_solicitud, estado
```

### Crear transferencia
```
POST /api/v1/inventario/transferencias/
Body: {
  "empresa": 1,
  "almacen_origen": 1,
  "almacen_destino": 2,
  "numero_transferencia": "TRF-001",
  "motivo": "Reabastecimiento",
  "usuario_solicitante": 1
}
```

### Enviar transferencia
```
POST /api/v1/inventario/transferencias/{id}/enviar/
```
Marca la transferencia como enviada y registra movimientos de salida

### Recibir transferencia
```
POST /api/v1/inventario/transferencias/{id}/recibir/
```
Marca la transferencia como recibida y registra movimientos de entrada

### Detalles de transferencia
```
GET /api/v1/inventario/transferencias/{id}/detalles/
POST /api/v1/inventario/transferencias-detalles/
```

---

## 8. Ajustes de Inventario

### Listar ajustes
```
GET /api/v1/inventario/ajustes/
Query params:
  - estado: Filtrar por estado (PENDIENTE, APROBADO, RECHAZADO, PROCESADO)
  - search: Búsqueda por motivo o nombre de almacén
  - ordering: Ordenar por fecha_ajuste, estado
```

### Crear ajuste
```
POST /api/v1/inventario/ajustes/
Body: {
  "empresa": 1,
  "almacen": 1,
  "tipo_ajuste": "AJUSTE_DIFERENCIA",
  "motivo": "Diferencia encontrada en conteo",
  "fecha_ajuste": "2024-12-01",
  "usuario_solicitante": 1
}
```

### Aprobar ajuste
```
POST /api/v1/inventario/ajustes/{id}/aprobar/
Body: {
  "observaciones": "Aprobado por supervisor"
}
```

### Rechazar ajuste
```
POST /api/v1/inventario/ajustes/{id}/rechazar/
Body: {
  "observaciones": "Motivo del rechazo"
}
```

### Procesar ajuste
```
POST /api/v1/inventario/ajustes/{id}/procesar/
```
Aplica los cambios al inventario (solo ajustes aprobados)

### Detalles de ajuste
```
GET /api/v1/inventario/ajustes/{id}/detalles/
POST /api/v1/inventario/ajustes-detalles/
Body: {
  "ajuste": 1,
  "producto": 1,
  "lote": 1,
  "cantidad_anterior": 100.00,
  "cantidad_nueva": 95.00,
  "costo_unitario": 50.00
}
```

---

## 9. Conteos Físicos

### Listar conteos
```
GET /api/v1/inventario/conteos-fisicos/
Query params:
  - estado: Filtrar por estado (PLANIFICADO, EN_PROCESO, FINALIZADO, AJUSTADO)
  - search: Búsqueda por número de conteo o nombre de almacén
  - ordering: Ordenar por fecha_conteo, estado
```

### Crear conteo
```
POST /api/v1/inventario/conteos-fisicos/
Body: {
  "empresa": 1,
  "almacen": 1,
  "numero_conteo": "CNT-001",
  "fecha_conteo": "2024-12-01",
  "tipo_conteo": "COMPLETO",
  "usuario_responsable": 1,
  "observaciones": "Conteo mensual"
}
```

### Iniciar conteo
```
POST /api/v1/inventario/conteos-fisicos/{id}/iniciar/
```

### Finalizar conteo
```
POST /api/v1/inventario/conteos-fisicos/{id}/finalizar/
```

### Ajustar inventario desde conteo
```
POST /api/v1/inventario/conteos-fisicos/{id}/ajustar/
```
Crea ajustes automáticos basados en las diferencias encontradas

### Detalles de conteo
```
GET /api/v1/inventario/conteos-fisicos/{id}/detalles/
POST /api/v1/inventario/conteos-fisicos-detalles/
Body: {
  "conteo": 1,
  "producto": 1,
  "lote": 1,
  "cantidad_sistema": 100.00,
  "cantidad_fisica": 95.00,
  "contado_por": 1,
  "observaciones": "Diferencia encontrada"
}
```

---

## Resumen de Endpoints

| Endpoint | Métodos | Descripción |
|----------|---------|-------------|
| `/almacenes/` | GET, POST, PUT, PATCH, DELETE | Gestión de almacenes |
| `/inventario/existencias/` | GET, PUT, PATCH | Consulta y actualización de existencias |
| `/inventario/movimientos/` | GET, POST, PUT, PATCH, DELETE | Gestión de movimientos |
| `/inventario/movimientos/kardex/` | GET | Historial con saldo acumulado |
| `/inventario/reservas/` | GET, POST, PUT, PATCH, DELETE | Gestión de reservas de stock |
| `/inventario/reservas/{id}/confirmar/` | POST | Confirmar reserva |
| `/inventario/reservas/{id}/cancelar/` | POST | Cancelar reserva |
| `/inventario/lotes/` | GET, POST, PUT, PATCH, DELETE | Gestión de lotes |
| `/inventario/alertas/` | GET, POST, PUT, PATCH, DELETE | Gestión de alertas |
| `/inventario/alertas/{id}/resolver/` | POST | Resolver alerta |
| `/inventario/alertas/generar_alertas/` | POST | Generar todas las alertas |
| `/inventario/transferencias/` | GET, POST, PUT, PATCH, DELETE | Gestión de transferencias |
| `/inventario/transferencias/{id}/enviar/` | POST | Enviar transferencia |
| `/inventario/transferencias/{id}/recibir/` | POST | Recibir transferencia |
| `/inventario/ajustes/` | GET, POST, PUT, PATCH, DELETE | Gestión de ajustes |
| `/inventario/ajustes/{id}/aprobar/` | POST | Aprobar ajuste |
| `/inventario/ajustes/{id}/rechazar/` | POST | Rechazar ajuste |
| `/inventario/ajustes/{id}/procesar/` | POST | Procesar ajuste |
| `/inventario/conteos-fisicos/` | GET, POST, PUT, PATCH, DELETE | Gestión de conteos |
| `/inventario/conteos-fisicos/{id}/iniciar/` | POST | Iniciar conteo |
| `/inventario/conteos-fisicos/{id}/finalizar/` | POST | Finalizar conteo |
| `/inventario/conteos-fisicos/{id}/ajustar/` | POST | Ajustar inventario desde conteo |

---

## Notas Importantes

1. **Idempotencia**: Los endpoints que crean recursos críticos (movimientos, transferencias, ajustes, conteos) soportan `idempotency_key` en el header `X-Idempotency-Key` o en el body.

2. **Filtrado por Empresa**: Todos los endpoints filtran automáticamente por empresa si está disponible en el request (requiere middleware de empresa).

3. **Permisos**: Todos los endpoints requieren autenticación y permisos específicos según el modelo.

4. **Transacciones**: Las operaciones críticas (procesar ajustes, recibir transferencias, etc.) se ejecutan dentro de transacciones atómicas.





