# Autenticación Multiempresa

## Descripción

El sistema implementa un flujo de autenticación en dos pasos donde primero se identifica la empresa y luego se autentican las credenciales del usuario.

## Flujo de Autenticación

### Paso 1: Identificar Empresa (Opcional)
Antes del login, se puede validar que la empresa existe:

```http
POST /api/v1/auth/validar-empresa/
Content-Type: application/json

{
  "empresa_username": "Mi Empresa SRL"
}
```

**Respuesta exitosa:**
```json
{
  "valida": true,
  "empresa": {
    "id": 1,
    "nombre": "Mi Empresa SRL",
    "rnc": "123456789"
  }
}
```

**Respuesta de error:**
```json
{
  "empresa_username": ["Empresa no encontrada o inactiva."]
}
```

### Paso 2: Login con Empresa y Credenciales

```http
POST /api/v1/auth/token/
Content-Type: application/json

{
  "empresa_username": "Mi Empresa SRL",
  "username": "usuario123",
  "password": "contraseña123"
}
```

**Respuesta exitosa:**
```json
{
  "refresh": "eyJ0eXAiOiJKV1QiLCJhbGc...",
  "access": "eyJ0eXAiOiJKV1QiLCJhbGc...",
  "user": {
    "id": 1,
    "username": "usuario123",
    "email": "usuario@example.com",
    "rol": "facturador",
    "empresa": {
      "id": 1,
      "nombre": "Mi Empresa SRL",
      "rnc": "123456789"
    }
  }
}
```

**Errores posibles:**

1. Empresa no encontrada:
```json
{
  "empresa_username": ["Empresa no encontrada o inactiva."]
}
```

2. Credenciales inválidas:
```json
{
  "username": ["Credenciales inválidas."]
}
```

3. Usuario no pertenece a la empresa:
```json
{
  "empresa_username": ["El usuario no pertenece a esta empresa."]
}
```

## Token JWT

El token JWT incluye información adicional:

```json
{
  "token_type": "access",
  "exp": 1234567890,
  "iat": 1234567890,
  "jti": "...",
  "user_id": 1,
  "username": "usuario123",
  "rol": "facturador",
  "empresa_id": 1,
  "empresa_nombre": "Mi Empresa SRL"
}
```

## Refresh Token

Para renovar el token de acceso:

```http
POST /api/v1/auth/token/refresh/
Content-Type: application/json

{
  "refresh": "eyJ0eXAiOiJKV1QiLCJhbGc..."
}
```

**Respuesta:**
```json
{
  "access": "eyJ0eXAiOiJKV1QiLCJhbGc..."
}
```

## Uso en el Frontend

### Ejemplo con JavaScript/TypeScript

```typescript
// Paso 1: Validar empresa (opcional)
async function validarEmpresa(nombreEmpresa: string) {
  const response = await fetch('/api/v1/auth/validar-empresa/', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({
      empresa_username: nombreEmpresa
    })
  });
  
  if (response.ok) {
    const data = await response.json();
    return data.empresa;
  }
  
  throw new Error('Empresa no encontrada');
}

// Paso 2: Login
async function login(empresaNombre: string, username: string, password: string) {
  const response = await fetch('/api/v1/auth/token/', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({
      empresa_username: empresaNombre,
      username: username,
      password: password
    })
  });
  
  if (response.ok) {
    const data = await response.json();
    // Guardar tokens
    localStorage.setItem('access_token', data.access);
    localStorage.setItem('refresh_token', data.refresh);
    localStorage.setItem('user', JSON.stringify(data.user));
    return data;
  }
  
  const error = await response.json();
  throw error;
}

// Uso
try {
  // Validar empresa primero
  const empresa = await validarEmpresa('Mi Empresa SRL');
  
  // Luego hacer login
  const authData = await login('Mi Empresa SRL', 'usuario123', 'contraseña123');
  console.log('Login exitoso:', authData.user);
} catch (error) {
  console.error('Error en login:', error);
}
```

### Ejemplo con React Hook Form

```tsx
import { useForm } from 'react-hook-form';

interface LoginForm {
  empresa_username: string;
  username: string;
  password: string;
}

function LoginForm() {
  const { register, handleSubmit, formState: { errors } } = useForm<LoginForm>();
  
  const onSubmit = async (data: LoginForm) => {
    try {
      const response = await fetch('/api/v1/auth/token/', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(data)
      });
      
      if (response.ok) {
        const authData = await response.json();
        // Guardar tokens y redirigir
        localStorage.setItem('access_token', authData.access);
        // ... resto del manejo
      }
    } catch (error) {
      console.error('Error:', error);
    }
  };
  
  return (
    <form onSubmit={handleSubmit(onSubmit)}>
      <input
        {...register('empresa_username', { required: true })}
        placeholder="Nombre de la empresa"
      />
      <input
        {...register('username', { required: true })}
        placeholder="Usuario"
      />
      <input
        {...register('password', { required: true })}
        type="password"
        placeholder="Contraseña"
      />
      <button type="submit">Iniciar Sesión</button>
    </form>
  );
}
```

## Configuración de Usuarios

### Asignar Empresa a Usuario

Los usuarios deben tener una empresa asignada para poder hacer login. Esto se puede hacer:

1. **Desde el Admin de Django:**
   - Ir a Usuarios → Seleccionar usuario → Asignar empresa

2. **Desde la API (requiere permisos de admin):**
   ```http
   PATCH /api/v1/usuarios/{id}/
   Authorization: Bearer {token}
   Content-Type: application/json

   {
     "empresa": 1
   }
   ```

## Seguridad

- Los usuarios solo pueden hacer login si pertenecen a la empresa especificada
- Las empresas inactivas no permiten login
- Los usuarios inactivos no pueden hacer login
- El token incluye información de la empresa para validación en cada request

## Notas Importantes

1. El campo `empresa_username` debe ser el **nombre exacto** de la empresa (no el RNC)
2. El usuario debe tener una empresa asignada en su perfil
3. La empresa debe estar activa (`activo=True`)
4. El usuario debe estar activo (`is_active=True`)

## Migración

Para aplicar los cambios:

```bash
python manage.py migrate usuarios
```

Esto agregará el campo `empresa` al modelo `User`.

