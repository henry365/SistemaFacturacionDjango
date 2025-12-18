# Sistema de Facturación Django + Next.js

[![Django Tests](https://github.com/henry365/SistemaFacturacionDjango/actions/workflows/tests.yml/badge.svg)](https://github.com/henry365/SistemaFacturacionDjango/actions/workflows/tests.yml)

Sistema de facturación completo para República Dominicana.

## Estructura del Proyecto

- `backend/`: Proyecto Django REST Framework.
- `frontend/`: Proyecto Next.js (App Router).
- `docker-compose.yml`: Configuración de base de datos PostgreSQL.

## Configuración Inicial

### Backend

1.  Navegar a la carpeta `backend`:
    ```bash
    cd backend
    ```

2.  Crear entorno virtual e instalar dependencias:
    ```bash
    python -m venv venv
    .\venv\Scripts\activate  # Windows
    # source venv/bin/activate # Linux/Mac
    pip install -r requirements.txt
    ```

3.  Configurar variables de entorno:
    - Copiar `.env` y ajustar si es necesario (por defecto usa SQLite para desarrollo rápido).
    - Para usar PostgreSQL, asegurar que los contenedores estén corriendo.

4.  Ejecutar migraciones:
    ```bash
    python manage.py migrate
    ```

5.  Crear superusuario (Administrador):
    ```bash
    # Opción 1: Interactivo
    python manage.py createsuperuser

    # Opción 2: Script automático (admin/admin123)
    Get-Content create_superuser.py | python manage.py shell
    ```

6.  Iniciar servidor de desarrollo:
    ```bash
    python manage.py runserver
    ```
    API disponible en: `http://localhost:8000/api/v1/`

### Frontend

1.  Navegar a la carpeta `frontend`:
    ```bash
    cd frontend
    ```

2.  Instalar dependencias:
    ```bash
    npm install
    ```

3.  Iniciar servidor de desarrollo:
    ```bash
    npm run dev
    ```
    Frontend disponible en: `http://localhost:3000`

## Módulos Implementados (Modelos)

- **Clientes**: Gestión de clientes.
- **Proveedores**: Gestión de proveedores.
- **Productos**: Productos, Servicios y Categorías.
- **Inventario**: Almacenes, Movimientos, Existencias.
- **Compras**: Solicitudes, Órdenes de Compra, Facturas de Proveedor.
- **Ventas**: Cotizaciones, Facturas, Pagos en Caja, Notas de Crédito/Débito.
- **Despachos**: Control de salidas de almacén.
- **Usuarios**: Gestión de usuarios y roles personalizados.

## API Endpoints (Ejemplos)

- `GET /api/v1/clientes/`: Listar clientes.
- `GET /api/v1/productos/`: Listar productos.
- `POST /api/v1/auth/token/`: Obtener token JWT.
