# 📡 API - Documentación de Endpoints

Sistema de API REST con FastAPI que incluye autenticación JWT, CRUD completo y validaciones robustas.

**Base URL por defecto**: `http://localhost:8000`

Todos los endpoints devuelven códigos de estado HTTP correctos (200/201/400/401/403/404/422/503).

---

## Índice de Contenidos

1. [Autenticación](#autenticación)
2. [Endpoints Públicos](#endpoints-públicos)
3. [Endpoints de Productos](#endpoints-de-productos)
4. [Endpoints de Empresas](#endpoints-de-empresas)
5. [Protección de Endpoints](#protección-de-endpoints)
6. [Uso de Tokens](#uso-de-tokens)
7. [Gestión de Usuarios](#gestión-de-usuarios)
8. [Códigos de Estado](#códigos-de-estado)

---

## Autenticación

### Descripción General

El sistema utiliza:
- **JWT (JSON Web Tokens)** para gestión de sesiones
- **bcrypt** para hash seguro de contraseñas
- **FastAPI dependencies** para proteger endpoints

### Variables de Entorno Requeridas

```env
SECRET_KEY=genera_una_clave_secreta_aleatoria
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=1440
```

Generar clave secreta:
```bash
openssl rand -hex 32
```

### Usuario Admin por Defecto (Desarrollo)

En modo desarrollo (`ENVIRONMENT=development`), se crea automáticamente un usuario administrador:

**Credenciales:**
- **Username**: `admin`
- **Email**: `admin@ejemplo.com`
- **Password**: `admin123`

**Uso:**
```bash
curl -X POST "http://localhost:8000/auth/login" \
  -H "Content-Type: application/json" \
  -d '{"email": "admin@ejemplo.com", "password": "admin123"}'
```

⚠️ **Este usuario solo existe en desarrollo. En producción debes crear usuarios manualmente.**

### Login

**POST** `/auth/login`

Autentica usuario y retorna token JWT.

**Request:**
```json
{
  "email": "usuario@ejemplo.com",
  "password": "password123"
}
```

**Response (200 OK):**
```json
{
  "access_token": "eyJ0eXAiOiJKV1QiLCJhbGc...",
  "token_type": "bearer",
  "expires_in": 86400,
  "user_id": 1,
  "username": "usuario123",
  "email": "usuario@ejemplo.com"
}
```

**Errores:**
- `401 Unauthorized`: Email o contraseña incorrectos
- `403 Forbidden`: Usuario inactivo

### Obtener Perfil

**GET** `/auth/me`

Retorna información del usuario autenticado.

**Headers:**
```
Authorization: Bearer <token>
```

**Response (200 OK):**
```json
{
  "id": 1,
  "username": "usuario123",
  "email": "usuario@ejemplo.com",
  "nombre": "Juan",
  "apellido": "Pérez"
}
```

### Cambiar Contraseña

**POST** `/auth/change-password`

Cambia la contraseña del usuario autenticado.

**Headers:**
```
Authorization: Bearer <token>
```

**Request:**
```json
{
  "current_password": "password_actual",
  "new_password": "nueva_password123"
}
```

**Response (200 OK):**
```json
{
  "message": "Contraseña actualizada exitosamente"
}
```

**Errores:**
- `400 Bad Request`: Contraseña actual incorrecta
- `401 Unauthorized`: Token inválido

**Validaciones de Contraseña:**
- Mínimo 8 caracteres
- Al menos una letra
- Al menos un número

### Estructura del Token JWT

El token contiene:
```json
{
  "user_id": 1,
  "username": "usuario123",
  "email": "usuario@ejemplo.com",
  "tipo_usuario_id": 2,
  "exp": 1699999999
}
```

---

## Endpoints Públicos

### Bienvenida

**GET** `/`

Retorna información general de la API.

**Response (200 OK):**
```json
{
  "message": "Bienvenido al Sistema de Inventario",
  "version": "1.0.0",
  "docs": "/docs"
}
```

### Health Check

**GET** `/health`

Verifica estado de la aplicación y conexión a base de datos.

**Response (200 OK):**
```json
{
  "status": "healthy",
  "database": "connected"
}
```

**Response (503 Service Unavailable):**
```json
{
  "status": "unhealthy",
  "database": "disconnected",
  "error": "Database connection failed"
}
```

### Información de Base de Datos

**GET** `/db/info`

Retorna información sobre la base de datos (sin credenciales).

**Response (200 OK):**
```json
{
  "database_url": "sqlite:///./inventario.db",
  "tables": ["usuarios", "productos", "empresas", "ventas"],
  "total_tables": 15
}
```

### Estadísticas Generales

**GET** `/stats`

Retorna estadísticas del sistema.

**Response (200 OK):**
```json
{
  "total_productos": 150,
  "total_empresas": 25,
  "total_usuarios": 10
}
```

---

## Endpoints de Productos

### Listar Productos

**GET** `/productos?skip=0&limit=10`

Lista productos con paginación.

**Query Parameters:**
- `skip` (int): Registros a saltar (≥ 0)
- `limit` (int): Registros a retornar (≥ 1)

**Response (200 OK):**
```json
[
  {
    "id": 1,
    "codigo": "PROD-001",
    "nombre": "Laptop Test",
    "descripcion": "Laptop de prueba",
    "marca": "TestBrand",
    "modelo": "X-100",
    "precio_compra": 800.0,
    "precio_venta": 1000.0,
    "stock_minimo": 5,
    "unidad_medida": "pza",
    "tipo_producto_id": 1,
    "estado_producto_id": 1
  }
]
```

**Errores:**
- `422 Unprocessable Entity`: Si `skip < 0` o `limit < 1`

### Obtener Producto

**GET** `/productos/{id}`

Obtiene un producto específico por ID.

**Response (200 OK):**
```json
{
  "id": 1,
  "codigo": "PROD-001",
  "nombre": "Laptop Test",
  ...
}
```

**Errores:**
- `404 Not Found`: Producto no existe

### Crear Producto

**POST** `/productos`

Crea un nuevo producto.

**Request:**
```json
{
  "codigo": "PROD-001",
  "nombre": "Laptop Test",
  "descripcion": "Laptop de prueba",
  "marca": "TestBrand",
  "modelo": "X-100",
  "precio_compra": 800.0,
  "precio_venta": 1000.0,
  "stock_minimo": 5,
  "unidad_medida": "pza",
  "tipo_producto_id": 1,
  "estado_producto_id": 1
}
```

**Response (201 Created):**
```json
{
  "id": 1,
  "codigo": "PROD-001",
  ...
}
```

**Errores:**
- `400 Bad Request`: Código duplicado
- `422 Unprocessable Entity`: Datos inválidos

### Actualizar Producto

**PUT** `/productos/{id}`

Actualiza un producto existente (actualización parcial permitida).

**Request:**
```json
{
  "nombre": "Producto Actualizado",
  "precio_venta": 175.0
}
```

**Response (200 OK):**
```json
{
  "id": 1,
  "nombre": "Producto Actualizado",
  "precio_venta": 175.0,
  ...
}
```

**Errores:**
- `404 Not Found`: Producto no existe

### Eliminar Producto

**DELETE** `/productos/{id}`

Elimina un producto.

**Response (200 OK):**
```json
{
  "message": "Producto eliminado exitosamente"
}
```

**Errores:**
- `404 Not Found`: Producto no existe

### Buscar Productos

**GET** `/productos/buscar/{termino}?skip=0&limit=10`

Busca productos por término en múltiples campos.

**Búsqueda en:**
- `nombre`
- `codigo`
- `descripcion`
- `marca`

**Response (200 OK):**
```json
[
  {
    "id": 1,
    "nombre": "Laptop HP",
    "codigo": "LAP-001",
    ...
  }
]
```

---

## Endpoints de Empresas

### Listar Empresas

**GET** `/empresas?skip=0&limit=10`

Lista empresas con paginación.

**Response (200 OK):**
```json
[
  {
    "id": 1,
    "nombre": "Empresa Test S.A.",
    "ruc": "20123456789",
    "direccion": "Av. Test 123",
    "telefono": "555-1234",
    "email": "contacto@empresatest.com",
    "contacto_principal": "Juan Pérez",
    "tipo_empresa_id": 1,
    "estado_empresa_id": 1
  }
]
```

### Crear Empresa

**POST** `/empresas`

Crea una nueva empresa.

**Request:**
```json
{
  "nombre": "Empresa Test S.A.",
  "ruc": "20123456789",
  "direccion": "Av. Test 123",
  "telefono": "555-1234",
  "email": "contacto@empresatest.com",
  "contacto_principal": "Juan Pérez",
  "tipo_empresa_id": 1,
  "estado_empresa_id": 1
}
```

**Response (201 Created):**
```json
{
  "id": 1,
  "nombre": "Empresa Test S.A.",
  ...
}
```

**Errores:**
- `400 Bad Request`: RUC duplicado
- `422 Unprocessable Entity`: Datos inválidos

---

## Protección de Endpoints

### Uso Básico - Usuario Autenticado

Para proteger un endpoint y requerir autenticación:

```python
from fastapi import Depends
from app.src.auth import get_current_user
from app.database.models import Usuario

@app.get("/users/me")
def get_my_profile(current_user: Usuario = Depends(get_current_user)):
    return {
        "id": current_user.id,
        "username": current_user.username,
        "email": current_user.email
    }
```

### Solo Administradores

Para restringir a usuarios administradores:

```python
from app.src.auth import get_current_admin

@app.get("/admin/dashboard")
def admin_dashboard(admin: Usuario = Depends(get_current_admin)):
    return {"message": "Panel de administrador"}
```

### Roles Personalizados

Para verificar roles específicos:

```python
from app.src.auth import require_role

# Crear dependencia para roles específicos
get_manager_or_admin = require_role([1, 2])  # IDs de tipos de usuario

@app.get("/reports")
def get_reports(user: Usuario = Depends(get_manager_or_admin)):
    return {"message": "Reportes"}
```

### Autenticación Opcional

Para endpoints que funcionan con o sin autenticación:

```python
from app.src.auth import get_optional_user

@app.get("/products")
def list_products(current_user: Usuario | None = Depends(get_optional_user)):
    if current_user:
        # Usuario autenticado - mostrar precios
        return {"products": [...], "show_prices": True}
    else:
        # Usuario anónimo - ocultar precios
        return {"products": [...], "show_prices": False}
```

### Referencia de Dependencias

| Dependencia | Descripción | Uso |
|-------------|-------------|-----|
| `get_current_user` | Usuario autenticado | Endpoints protegidos |
| `get_optional_user` | Usuario opcional | Endpoints públicos con funcionalidad extra |
| `get_current_admin` | Solo administradores | Endpoints de administración |
| `require_role([ids])` | Roles específicos | Permisos personalizados |

---

## Uso de Tokens

### Con cURL

```bash
# 1. Obtener token
TOKEN=$(curl -X POST "http://localhost:8000/auth/login" \
  -H "Content-Type: application/json" \
  -d '{"email": "user@example.com", "password": "pass123"}' \
  | jq -r '.access_token')

# 2. Usar el token
curl -X GET "http://localhost:8000/auth/me" \
  -H "Authorization: Bearer $TOKEN"
```

### Con Python Requests

```python
import requests

# Login
response = requests.post(
    "http://localhost:8000/auth/login",
    json={"email": "user@example.com", "password": "pass123"}
)
token = response.json()["access_token"]

# Usar token
headers = {"Authorization": f"Bearer {token}"}
response = requests.get(
    "http://localhost:8000/auth/me",
    headers=headers
)
```

### Con JavaScript/Fetch

```javascript
// Login
const response = await fetch('http://localhost:8000/auth/login', {
  method: 'POST',
  headers: {'Content-Type': 'application/json'},
  body: JSON.stringify({
    email: 'user@example.com',
    password: 'pass123'
  })
});
const {access_token} = await response.json();

// Usar token
const userResponse = await fetch('http://localhost:8000/auth/me', {
  headers: {'Authorization': `Bearer ${access_token}`}
});
```

---

## Gestión de Usuarios

### Crear Usuario

```python
from app.src.auth import crud_usuario
from app.database.schemas import UsuarioCreate

usuario_data = UsuarioCreate(
    username="nuevo_usuario",
    email="nuevo@ejemplo.com",
    password="password123",  # Se hasheará automáticamente
    nombre="Juan",
    apellido="Pérez",
    tipo_usuario_id=1,
    estado_usuario_id=1
)

usuario = crud_usuario.create(db=db, obj_in=usuario_data)
```

### Cambiar Contraseña Programáticamente

```python
from app.src.auth import crud_usuario

success = crud_usuario.change_password(
    db=db,
    usuario_id=usuario.id,
    current_password="password_actual",
    new_password="nueva_password123"
)

if not success:
    print("Contraseña actual incorrecta")
```

### Ejemplo Completo de Router

```python
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.database.database import get_db
from app.database.models import Usuario
from app.src.auth import (
    auth_service,
    LoginRequest,
    get_current_user,
    get_current_admin,
    ChangePasswordRequest,
    crud_usuario
)

router = APIRouter(prefix="/auth", tags=["Autenticación"])

@router.post("/login")
def login(login_data: LoginRequest, db: Session = Depends(get_db)):
    """Login con email y password"""
    return auth_service.login(db=db, login_data=login_data)

@router.get("/me")
def get_my_profile(current_user: Usuario = Depends(get_current_user)):
    """Obtener perfil del usuario actual"""
    return {
        "id": current_user.id,
        "username": current_user.username,
        "email": current_user.email,
        "nombre": current_user.nombre,
        "apellido": current_user.apellido
    }

@router.post("/change-password")
def change_password(
    password_data: ChangePasswordRequest,
    current_user: Usuario = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Cambiar contraseña del usuario actual"""
    success = crud_usuario.change_password(
        db=db,
        usuario_id=current_user.id,
        current_password=password_data.current_password,
        new_password=password_data.new_password
    )
    
    if not success:
        raise HTTPException(status_code=400, detail="Contraseña actual incorrecta")
    
    return {"message": "Contraseña actualizada exitosamente"}
```

---

## Códigos de Estado

### Respuestas Exitosas

| Código | Descripción |
|--------|-------------|
| 200 OK | Operación exitosa (GET, PUT, DELETE) |
| 201 Created | Recurso creado exitosamente (POST) |

### Errores del Cliente

| Código | Descripción | Ejemplo |
|--------|-------------|---------|
| 400 Bad Request | Datos duplicados o violación de reglas de negocio | Código/RUC duplicado |
| 401 Unauthorized | Credenciales inválidas o token expirado | Login fallido, token inválido |
| 403 Forbidden | Usuario sin permisos o inactivo | Usuario inactivo, sin rol requerido |
| 404 Not Found | Recurso no encontrado | Producto/empresa no existe |
| 422 Unprocessable Entity | Validación de datos fallida | Formato inválido, campos requeridos |

### Errores del Servidor

| Código | Descripción |
|--------|-------------|
| 503 Service Unavailable | Servicio no disponible (BD desconectada) |

---

## Notas Importantes

### Serialización de Datos

- **Precios**: Se serializan como números (no strings)
  ```json
  {
    "precio_compra": 800.0,
    "precio_venta": 1000.0
  }
  ```

### CORS

- Configurado con variable `ALLOWED_ORIGINS`
- Permite solicitudes desde orígenes especificados
- Ver `config.md` para configuración

### Creación de Tablas

- Tablas se crean automáticamente en `startup`
- No requiere migración manual inicial

### Paginación

- `skip`: Debe ser ≥ 0
- `limit`: Debe ser ≥ 1
- Valores inválidos retornan 422

---

## Flujo de Autenticación

```
1. Cliente → POST /auth/login {email, password}
2. Servidor → Verifica credenciales en BD
3. Servidor → Genera token JWT
4. Servidor → Retorna token + datos usuario
5. Cliente → Almacena token
6. Cliente → Incluye token en header: "Authorization: Bearer <token>"
7. Servidor → Valida token en cada request
8. Servidor → Retorna datos solicitados
```

---

## Seguridad

### Buenas Prácticas

1. **Nunca** guardes `SECRET_KEY` en el código fuente
2. Usa variables de entorno para configuración sensible
3. Los tokens expiran en 24 horas por defecto (configurable)
4. Las contraseñas se hashean con bcrypt (nunca texto plano)
5. Validación automática de usuario activo en cada request

### Archivos de Autenticación

- `app/src/auth/jwt.py` - JWTHandler (crear/verificar/decodificar tokens)
- `app/src/auth/password.py` - PasswordHandler (hash/verificación)
- `app/src/auth/crud.py` - CRUDUsuario (operaciones BD)
- `app/src/auth/service.py` - AuthService (lógica de negocio)
- `app/src/auth/dependencies.py` - Dependencias FastAPI

---

## Troubleshooting

### Error: "Could not validate credentials"
- Verificar que el token esté en el header `Authorization: Bearer <token>`
- Verificar que el token no haya expirado
- Verificar que la `SECRET_KEY` sea la correcta

### Error: "User inactive"
- El usuario existe pero su estado está inactivo
- Verificar `estado_usuario.activo = True` en la base de datos

### Error: "Incorrect email or password"
- Las credenciales son incorrectas
- Verificar que el email y password sean correctos
