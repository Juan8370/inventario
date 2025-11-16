# 🚀 Instalación y Configuración

Guía completa para configurar el entorno de desarrollo, instalar dependencias, ejecutar la aplicación y correr pruebas.

---

## Índice de Contenidos

1. [Requisitos Previos](#requisitos-previos)
2. [Instalación](#instalación)
3. [Configuración](#configuración)
4. [Ejecución](#ejecución)
5. [Pruebas](#pruebas)
6. [Estructura del Proyecto](#estructura-del-proyecto)
7. [Troubleshooting](#troubleshooting)

---

## Requisitos Previos

### Software Requerido

- **Python 3.11+** (probado con 3.14)
- **pip** (gestor de paquetes de Python)
- **Git** (opcional, para clonar el repositorio)

### Sistema Operativo

- Windows 10/11 con PowerShell 5.1+
- Linux/macOS (comandos pueden variar)

### Verificar Instalación

```powershell
# Verificar versión de Python
python --version
# o
py --version

# Verificar pip
pip --version
```

---

## Instalación

### 1. Clonar o Descargar el Proyecto

**Opción A: Con Git**
```powershell
git clone https://github.com/tu-usuario/inventario.git
cd inventario
```

**Opción B: Descarga directa**
- Descarga y descomprime el archivo ZIP
- Navega al directorio en PowerShell

### 2. Crear Entorno Virtual

Es altamente recomendado usar un entorno virtual para aislar las dependencias.

```powershell
# Crear entorno virtual
py -m venv .venv

# Activar entorno virtual (Windows PowerShell)
.\.venv\Scripts\Activate.ps1

# Para Linux/macOS
# source .venv/bin/activate
```

**Nota**: Si obtienes un error de política de ejecución en PowerShell:
```powershell
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
```

### 3. Instalar Dependencias

#### Instalación Básica (Producción)

```powershell
pip install -r requirements.txt
```

**Paquetes incluidos en `requirements.txt`:**
- `fastapi` - Framework web
- `uvicorn[standard]` - Servidor ASGI
- `sqlalchemy` - ORM
- `pydantic[email]` - Validación de datos
- `python-dotenv` - Variables de entorno
- `PyJWT` - Autenticación JWT
- `passlib[bcrypt]` - Hash de contraseñas
- `bcrypt` - Backend para passlib
- `email-validator` - Validación de emails

#### Instalación para Desarrollo

```powershell
pip install -r requirements-dev.txt
```

**Paquetes adicionales en `requirements-dev.txt`:**
- `pytest` - Framework de testing
- `httpx` - Cliente HTTP para tests
- `pytest-cov` - Cobertura de tests

---

## Configuración

### 1. Variables de Entorno

Configura variables con un archivo `.env` en la raíz del proyecto. Usa la plantilla de ejemplo:

```powershell
# Copiar archivo de ejemplo
Copy-Item .env.example .env
```

**Edita `.env` con tus valores:**

```env
# Base de datos
DATABASE_URL=sqlite:///./inventario.db

# Aplicación
APP_NAME=Sistema de Inventario
APP_DESCRIPTION=API para gestión de inventario
APP_VERSION=1.0.0
DEBUG=True
ENVIRONMENT=development

# Seguridad - IMPORTANTE: Cambiar en producción
SECRET_KEY=genera_una_clave_aleatoria_aqui
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=1440

# CORS (lista separada por comas)
ALLOWED_ORIGINS=http://localhost:3000,http://localhost:8080

# Semilla de datos (solo en dev)
SEED_DEV_ADMIN=true
```

**Generar SECRET_KEY segura:**

```powershell
# Con Python
python -c "import secrets; print(secrets.token_hex(32))"

# Con OpenSSL (si está instalado)
openssl rand -hex 32
```

Ver `config.md` para más detalles sobre configuración.

Notas importantes:

- En producción, la app no crea tablas automáticamente (usa migraciones/Alembic).
- La semilla del usuario admin solo corre si `ENVIRONMENT=development` y `SEED_DEV_ADMIN=true`.
- El logging es legible en dev y JSON en producción.

### 2. Base de Datos

#### SQLite (por defecto)

No requiere configuración adicional. El archivo `inventario.db` se creará automáticamente al iniciar la aplicación.

#### PostgreSQL (producción recomendada)

```env
DATABASE_URL=postgresql://usuario:password@localhost:5432/inventario
```

#### MySQL

```env
DATABASE_URL=mysql+pymysql://usuario:password@localhost:3306/inventario
```

---

## Ejecución

### Método 1: Script de Inicio (Recomendado)

```powershell
python run.py
# o
py run.py
```

### Método 2: Uvicorn Directo

```powershell
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### Acceder a la Aplicación

Una vez iniciada, la aplicación estará disponible en:

- **API Base**: <http://localhost:8000/>
- **Documentación Interactiva (Swagger)**: <http://localhost:8000/docs>
- **Documentación Alternativa (ReDoc)**: <http://localhost:8000/redoc>

### Usuario Admin por Defecto (solo desarrollo)

Si configuras `ENVIRONMENT=development` y `SEED_DEV_ADMIN=true`, se intentará crear un usuario admin inicial:

**Credenciales por defecto (cámbialas luego):**

- Username: `admin`
- Email: `admin@ejemplo.com`
- Password: `admin123`

La creación se omite si el usuario ya existe o si faltan tipos/estados base.

### Verificar Estado

```powershell
# Health check
curl http://localhost:8000/health

# Login con usuario admin
curl -X POST "http://localhost:8000/auth/login" \
  -H "Content-Type: application/json" \
  -d '{"email": "admin@ejemplo.com", "password": "admin123"}'

# Estadísticas (requiere autenticación)
curl http://localhost:8000/stats
```

---

## Pruebas

### Configuración de Pruebas

Las pruebas utilizan una base de datos en memoria (`sqlite:///:memory:`) para mayor velocidad y aislamiento.

**Archivos de prueba:**
- `test/test_database.py` - Estructura y operaciones de BD (9 tests)
- `test/test_auth.py` - Sistema de autenticación (34 tests)
- `test/test_api_endpoints.py` - Endpoints de API (22 tests)
- `test/conftest.py` - Configuración global de pytest

### Ejecutar Todas las Pruebas

```powershell
# Ejecutar todos los tests
pytest

# Con output verbose
pytest -v

# Con tracebacks cortos
pytest -v --tb=short
```

**Salida esperada:**
```
================================ test session starts =================================
collected 65 items

test/test_api_endpoints.py::test_read_root PASSED                          [  1%]
test/test_api_endpoints.py::test_health_endpoint PASSED                    [  3%]
...
test/test_auth.py::test_password_hash PASSED                               [ 52%]
...
test/test_database.py::test_tables_exist PASSED                            [ 92%]
...

================================= 65 passed in 21.45s ================================
```

### Ejecutar Pruebas Específicas

```powershell
# Solo pruebas de autenticación
pytest test/test_auth.py -v

# Solo pruebas de endpoints
pytest test/test_api_endpoints.py -v

# Solo pruebas de base de datos
pytest test/test_database.py -v

# Ejecutar un test específico
pytest test/test_auth.py::test_login_success -v
```

### Cobertura de Código

```powershell
# Ejecutar tests con cobertura
pytest --cov=app --cov-report=html

# Ver reporte en el navegador
# Abre: htmlcov/index.html
```

### Pruebas en CI/CD

Todas las pruebas están diseñadas para ejecutarse simultáneamente sin conflictos:

```powershell
# Ejecutar como en CI
pytest test/ -v --tb=short
```

**Características de las pruebas:**
- ✅ Base de datos en memoria (rápido, sin archivos)
- ✅ Aislamiento entre módulos de prueba
- ✅ Cleanup automático después de cada test
- ✅ Sin dependencias externas
- ✅ 100% determinísticas

---

## Estructura del Proyecto

```
inventario/
├── app/
│   ├── __init__.py
│   ├── main.py                 # Aplicación FastAPI principal
│   ├── database/
│   │   ├── __init__.py
│   │   ├── models.py           # Modelos SQLAlchemy
│   │   ├── schemas.py          # Schemas Pydantic
│   │   ├── database.py         # Configuración de BD
│   │   ├── crud.py             # Operaciones CRUD genéricas
│   │   └── db_driver.py        # Driver de base de datos
│   └── src/
│       └── auth/
│           ├── jwt.py          # Manejo de JWT
│           ├── password.py     # Hash de contraseñas
│           ├── crud.py         # CRUD de usuarios
│           ├── service.py      # Lógica de autenticación
│           └── dependencies.py # Dependencias FastAPI
│
├── test/
│   ├── __init__.py
│   ├── conftest.py             # Configuración pytest
│   ├── test_database.py        # Tests de BD
│   ├── test_auth.py            # Tests de autenticación
│   └── test_api_endpoints.py  # Tests de API
│
├── docs/
│   ├── database.md             # Documentación de BD
│   ├── api.md                  # Documentación de API
│   ├── config.md               # Configuración
│   └── setup.md                # Esta guía
│
├── .env                        # Variables de entorno (NO versionar)
├── .env.example                # Ejemplo de variables
├── .gitignore                  # Archivos ignorados por git
├── requirements.txt            # Dependencias de producción
├── requirements-dev.txt        # Dependencias de desarrollo
├── pytest.ini                  # Configuración de pytest
├── run.py                      # Script de inicio
└── README.md                   # Documentación principal
```

### Archivos Clave

| Archivo | Descripción |
|---------|-------------|
| `app/main.py` | Punto de entrada de la aplicación FastAPI |
| `app/database/models.py` | Definiciones de tablas SQLAlchemy |
| `app/database/schemas.py` | Validaciones Pydantic |
| `app/database/crud.py` | Clase `CRUDBase` para operaciones genéricas |
| `app/src/auth/*` | Sistema completo de autenticación JWT |
| `run.py` | Script simple para iniciar el servidor |
| `.env` | Configuración del entorno (NO versionar) |
| `pytest.ini` | Configuración de pytest |

---

## Troubleshooting

### Error: "ModuleNotFoundError"

**Problema**: Python no encuentra los módulos instalados.

**Solución**:
```powershell
# Verificar que el entorno virtual esté activado
# Deberías ver (.venv) al inicio del prompt

# Reinstalar dependencias
pip install -r requirements.txt
```

### Error: "Address already in use"

**Problema**: El puerto 8000 ya está siendo usado.

**Solución**:
```powershell
# Opción 1: Usar otro puerto
uvicorn app.main:app --reload --port 8001

# Opción 2: Matar el proceso que usa el puerto 8000
# Encontrar el proceso
netstat -ano | findstr :8000

# Matar el proceso (reemplaza PID con el número encontrado)
taskkill /PID <PID> /F
```

### Error: "Database is locked" (SQLite)

**Problema**: Múltiples procesos intentando acceder a la BD simultáneamente.

**Solución**:
```powershell
# Cerrar todos los procesos que usan la BD
# Borrar el archivo de BD si es necesario
Remove-Item inventario.db

# Reiniciar la aplicación
python run.py
```

### Pruebas Fallan en Windows

**Problema**: Problemas con permisos o archivos bloqueados.

**Solución**:
```powershell
# Asegurarte de que no haya procesos corriendo
# Las pruebas usan base de datos en memoria, no deberían crear archivos

# Si hay archivos de test residuales
Remove-Item test_*.db -Force

# Ejecutar pruebas nuevamente
pytest -v
```

### Error: "SECRET_KEY not configured"

**Problema**: No se encontró la variable `SECRET_KEY` en `.env`.

**Solución**:
```powershell
# Generar una clave
python -c "import secrets; print(secrets.token_hex(32))"

# Copiar el resultado y agregarlo a .env
# SECRET_KEY=resultado_aqui
```

### CORS Error en Frontend

**Problema**: El frontend no puede hacer requests a la API.

**Solución**:
```env
# En .env, agregar el origen del frontend
ALLOWED_ORIGINS=http://localhost:3000,http://localhost:8080

# Reiniciar el servidor después de cambiar .env
```

---

## Flujo de Trabajo de Desarrollo

### 1. Configuración Inicial (Una vez)

```powershell
# Clonar proyecto
git clone <repo>
cd inventario

# Crear entorno virtual
py -m venv .venv

# Activar entorno
.\.venv\Scripts\Activate.ps1

# Instalar dependencias
pip install -r requirements-dev.txt

# Configurar .env
Copy-Item .env.example .env
# Editar .env con tu configuración
```

### 2. Desarrollo Diario

```powershell
# Activar entorno (si no está activado)
.\.venv\Scripts\Activate.ps1

# Iniciar servidor en modo desarrollo
python run.py

# En otra terminal: ejecutar pruebas
pytest -v

# Cuando termines
# Ctrl+C para detener el servidor
# deactivate para desactivar el entorno
```

### 3. Antes de Commit

```powershell
# Ejecutar todas las pruebas
pytest -v

# Verificar cobertura
pytest --cov=app

# Si todo está OK, hacer commit
git add .
git commit -m "Descripción de cambios"
```

---

## Despliegue en Producción

### Preparación

1. **Configurar variables de entorno de producción**

```env
DEBUG=False
ENVIRONMENT=production
DATABASE_URL=postgresql://user:pass@host/db
SECRET_KEY=clave_aleatoria_segura
ALLOWED_ORIGINS=https://tu-dominio.com
ACCESS_TOKEN_EXPIRE_MINUTES=60
```

2. **Usar servidor de producción**

```powershell
# Instalar gunicorn (Linux) o waitress (Windows)
pip install gunicorn  # Linux
pip install waitress  # Windows

# Ejecutar con gunicorn (Linux)
gunicorn app.main:app -w 4 -k uvicorn.workers.UvicornWorker

# Ejecutar con waitress (Windows)
waitress-serve --port=8000 app.main:app
```

3. **Configurar proxy reverso** (Nginx/Apache)

4. **Configurar SSL/HTTPS**

5. **Configurar base de datos externa** (PostgreSQL recomendado)

---

## Recursos Adicionales

### Documentación Relacionada

- `database.md` - Esquema de base de datos y modelos
- `api.md` - Endpoints y autenticación
- `config.md` - Variables de entorno detalladas

### Enlaces Útiles

- [Documentación FastAPI](https://fastapi.tiangolo.com/)
- [Documentación SQLAlchemy](https://docs.sqlalchemy.org/)
- [Documentación Pydantic](https://docs.pydantic.dev/)
- [Documentación pytest](https://docs.pytest.org/)

### Comandos de Referencia Rápida

```powershell
# Activar entorno
.\.venv\Scripts\Activate.ps1

# Instalar dependencias
pip install -r requirements.txt

# Ejecutar aplicación
python run.py

# Ejecutar tests
pytest -v

# Ver cobertura
pytest --cov=app --cov-report=html

# Generar SECRET_KEY
python -c "import secrets; print(secrets.token_hex(32))"
```
