# Módulo de Usuarios y Seguridad Granular

## Descripción General

El módulo de usuarios gestiona la autenticación, autorización y gestión de usuarios del sistema con soporte multiempresa y seguridad granular basada en permisos y roles.

## Estructura del Módulo

### Modelos

#### User

Modelo de usuario personalizado que extiende `AbstractUser`.

**Campos:**
- `username` (CharField): Nombre de usuario único
- `email` (EmailField): Correo electrónico
- `first_name` (CharField): Nombre
- `last_name` (CharField): Apellido
- `rol` (CharField): Rol del usuario (admin, facturador, cajero, almacen, compras, contabilidad)
- `telefono` (CharField): Teléfono de contacto
- `empresa` (ForeignKey): Empresa a la que pertenece el usuario
- `is_active` (BooleanField): Indica si el usuario está activo
- `is_staff` (BooleanField): Indica si es staff/admin
- `date_joined` (DateTimeField): Fecha de registro

**Restricciones:**
- Email único por empresa
- Usuario con rol 'admin' automáticamente tiene `is_staff=True`

### Serializers

#### UserSerializer
Serializer para lectura y actualización de usuarios (sin password).

#### UserCreateSerializer
Serializer para crear usuarios con password. Incluye validación de complejidad de password.

#### UserUpdateSerializer
Serializer para actualizar usuarios sin modificar password.

#### ChangePasswordSerializer
Serializer para cambio de contraseña. Requiere contraseña actual.

#### GroupSerializer
Serializer para grupos/roles con contadores de permisos y usuarios.

#### PermissionSerializer
Serializer para permisos con información de app y modelo.

### Viewsets (API Endpoints)

#### UserViewSet

**Endpoint:** `/api/v1/usuarios/`

**Características:**
- Filtrado automático por empresa
- Usuarios normales solo pueden ver/editar su propio perfil
- Administradores pueden gestionar todos los usuarios de su empresa
- Búsqueda por username, email, nombre, apellido
- Ordenamiento por username, fecha de registro, rol

**Métodos HTTP:**
- `GET /api/v1/usuarios/` - Listar usuarios
- `POST /api/v1/usuarios/` - Crear usuario (admin)
- `GET /api/v1/usuarios/{id}/` - Obtener usuario
- `PUT /api/v1/usuarios/{id}/` - Actualizar usuario completo
- `PATCH /api/v1/usuarios/{id}/` - Actualizar usuario parcial
- `DELETE /api/v1/usuarios/{id}/` - Eliminar usuario (admin)

**Filtros Específicos:**
- `?activo=true/false` - Filtrar por estado activo
- `?rol=facturador` - Filtrar por rol
- `?empresa={id}` - Filtrar por empresa (solo admin)

**Acciones Personalizadas:**
- `GET /api/v1/usuarios/perfil/` - Obtener perfil del usuario autenticado
- `PATCH /api/v1/usuarios/actualizar_perfil/` - Actualizar perfil propio
- `POST /api/v1/usuarios/cambiar_password/` - Cambiar contraseña propia
- `POST /api/v1/usuarios/{id}/activar/` - Activar usuario (admin)
- `POST /api/v1/usuarios/{id}/desactivar/` - Desactivar usuario (admin)
- `POST /api/v1/usuarios/{id}/asignar_permisos/` - Asignar permisos a usuario (admin)
- `POST /api/v1/usuarios/{id}/quitar_permisos/` - Quitar permisos de usuario (admin)
- `POST /api/v1/usuarios/{id}/asignar_grupo/` - Asignar grupo/rol a usuario (admin)
- `POST /api/v1/usuarios/{id}/quitar_grupo/` - Quitar grupo/rol de usuario (admin)

#### GroupViewSet

**Endpoint:** `/api/v1/grupos/`

**Características:**
- Solo accesible para administradores
- Gestión completa de grupos/roles

**Métodos HTTP:**
- `GET /api/v1/grupos/` - Listar grupos
- `POST /api/v1/grupos/` - Crear grupo
- `GET /api/v1/grupos/{id}/` - Obtener grupo
- `PUT /api/v1/grupos/{id}/` - Actualizar grupo
- `DELETE /api/v1/grupos/{id}/` - Eliminar grupo

**Acciones Personalizadas:**
- `GET /api/v1/grupos/{id}/permisos/` - Listar permisos del grupo
- `POST /api/v1/grupos/{id}/asignar_permisos/` - Asignar permisos al grupo
- `POST /api/v1/grupos/{id}/quitar_permisos/` - Quitar permisos del grupo
- `GET /api/v1/grupos/{id}/usuarios/` - Listar usuarios del grupo

#### PermissionViewSet

**Endpoint:** `/api/v1/permisos/`

**Características:**
- Solo lectura
- Solo accesible para administradores
- Lista todos los permisos disponibles del sistema

**Métodos HTTP:**
- `GET /api/v1/permisos/` - Listar permisos
- `GET /api/v1/permisos/{id}/` - Obtener permiso

**Filtros:**
- `?app_label=clientes` - Filtrar por aplicación

## Sistema de Permisos Granulares

### Clases de Permisos

#### ActionBasedPermission
Mapea acciones de DRF a permisos de Django:
- `GET` → `view_model`
- `POST` → `add_model`
- `PUT/PATCH` → `change_model`
- `DELETE` → `delete_model`

Soporta permisos específicos en acciones personalizadas usando el decorador `@require_permission`.

#### IsAdminOrSameEmpresa
Permite a administradores acceso completo, o a usuarios normales solo objetos de su empresa.

#### IsOwnerOrReadOnly
Permite a usuarios ver/editar solo sus propios objetos.

#### HasPermissionOrReadOnly
Requiere un permiso específico para escritura, permite lectura.

### Decorador @require_permission

Permite asignar permisos específicos a acciones personalizadas:

```python
@action(detail=True, methods=['post'])
@require_permission('usuarios.change_user')
def activar(self, request, pk=None):
    ...
```

## Ejemplos de Uso

### Crear Usuario (Admin)

```http
POST /api/v1/usuarios/
Content-Type: application/json
Authorization: Bearer {token}

{
  "username": "nuevo_usuario",
  "email": "usuario@example.com",
  "password": "Contraseña123!",
  "password_confirm": "Contraseña123!",
  "first_name": "Juan",
  "last_name": "Pérez",
  "rol": "facturador",
  "telefono": "809-555-1234",
  "is_active": true
}
```

### Obtener Perfil Propio

```http
GET /api/v1/usuarios/perfil/
Authorization: Bearer {token}
```

### Actualizar Perfil Propio

```http
PATCH /api/v1/usuarios/actualizar_perfil/
Content-Type: application/json
Authorization: Bearer {token}

{
  "first_name": "Juan Carlos",
  "telefono": "809-555-5678"
}
```

### Cambiar Contraseña

```http
POST /api/v1/usuarios/cambiar_password/
Content-Type: application/json
Authorization: Bearer {token}

{
  "password_actual": "ContraseñaAntigua123!",
  "password_nuevo": "NuevaContraseña456!",
  "password_confirm": "NuevaContraseña456!"
}
```

### Asignar Grupo/Rol a Usuario (Admin)

```http
POST /api/v1/usuarios/1/asignar_grupo/
Content-Type: application/json
Authorization: Bearer {token}

{
  "grupo_nombre": "facturador"
}
```

### Asignar Permisos a Grupo (Admin)

```http
POST /api/v1/grupos/1/asignar_permisos/
Content-Type: application/json
Authorization: Bearer {token}

{
  "permisos": [1, 2, 3, 4]
}
```

### Listar Permisos Disponibles

```http
GET /api/v1/permisos/?app_label=clientes
Authorization: Bearer {token}
```

## Configuración de Roles

Los roles se configuran usando el comando de gestión:

```bash
python manage.py setup_roles
```

Este comando crea grupos con permisos predefinidos según el rol:
- **admin**: Todos los permisos
- **facturador**: Permisos para clientes, productos, ventas
- **cajero**: Permisos para facturas y pagos
- **almacen**: Permisos para inventario y productos
- **compras**: Permisos para compras y proveedores

## Seguridad

### Control de Acceso

1. **Multiempresa**: Los usuarios solo ven datos de su empresa
2. **Roles**: Los permisos se asignan por grupos/roles
3. **Permisos Granulares**: Permisos específicos por acción y modelo
4. **Verificación a Nivel de Objeto**: Permisos verificados tanto a nivel de vista como de objeto

### Validaciones

- Password con complejidad mínima (8 caracteres, validación Django)
- Email único por empresa
- Teléfono con formato válido
- Confirmación de password al crear/cambiar

## Notas de Implementación

### Cambios Recientes

1. **Sistema de permisos granular**: Soporte para permisos en acciones personalizadas
2. **ViewSets completos**: UserViewSet, GroupViewSet, PermissionViewSet
3. **Acciones personalizadas**: Perfil, cambio de contraseña, gestión de permisos
4. **Validaciones mejoradas**: Password, email, teléfono
5. **Admin mejorado**: Gestión de grupos y permisos

### Dependencias

- `empresas.Empresa`: Modelo de empresa (requerido)
- `django.contrib.auth.models.Group`: Grupos/roles
- `django.contrib.auth.models.Permission`: Permisos

## Próximas Mejoras Sugeridas

1. Implementar auditoría de cambios de permisos
2. Agregar notificaciones cuando se asignan/quitan permisos
3. Implementar permisos temporales con fecha de expiración
4. Agregar reportes de usuarios por rol y empresa
5. Implementar autenticación de dos factores (2FA)

