# ⚙️ Configuración - Variables de Entorno

La aplicación usa `pydantic-settings` (Pydantic v2) para cargar y validar configuración desde variables de entorno y archivo `.env` automáticamente mediante `app/core/settings.py`.

---

## Archivo .env

Copia desde `.env.example` y ajusta valores según tu entorno. `pydantic-settings` lo carga automáticamente, no necesitas llamar `load_dotenv()`.

### Ejemplo Completo

```env
# ===== BASE DE DATOS =====
DATABASE_URL=sqlite:///./inventario.db
# Ejemplos para otros motores:
# DATABASE_URL=postgresql://usuario:password@localhost/inventario
# DATABASE_URL=mysql+pymysql://usuario:password@localhost/inventario

# ===== APLICACIÓN =====
APP_NAME=Sistema de Inventario
APP_VERSION=1.0.0
APP_DESCRIPTION=API para gestión de inventario
DEBUG=True
ENVIRONMENT=development

# ===== SERVIDOR =====
HOST=0.0.0.0
PORT=8000
RELOAD=True

# ===== SEGURIDAD =====
# IMPORTANTE: Cambia SECRET_KEY en producción
SECRET_KEY=tu_clave_secreta_super_segura_cambiala_en_produccion
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=1440

# ===== CORS =====
# Lista separada por comas de orígenes permitidos
ALLOWED_ORIGINS=http://localhost:3000,http://localhost:8080

# ===== PAGINACIÓN =====
DEFAULT_PAGE_SIZE=10
MAX_PAGE_SIZE=100
```

---

## Variables Detalladas

### Base de Datos

| Variable | Descripción | Ejemplo | Requerido |
|----------|-------------|---------|-----------|
| `DATABASE_URL` | URL de conexión a la base de datos | `sqlite:///./inventario.db` | ✅ |

**Formatos soportados:**
- **SQLite**: `sqlite:///./nombre.db` (archivo local)
- **PostgreSQL**: `postgresql://user:pass@host:port/dbname`
- **MySQL**: `mysql+pymysql://user:pass@host:port/dbname`

**Nota para SQLite**: La ruta `sqlite:///./inventario.db` crea el archivo en el directorio donde se ejecuta `run.py`.

### Aplicación

| Variable | Descripción | Valor por Defecto |
|----------|-------------|-------------------|
| `APP_NAME` | Nombre de la aplicación | `Sistema de Inventario` |
| `APP_VERSION` | Versión de la API | `1.0.0` |
| `APP_DESCRIPTION` | Descripción breve | `API para gestión de inventario` |
| `DEBUG` | Modo debug (habilita logs detallados) | `True` |
| `ENVIRONMENT` | Entorno de ejecución | `development` |

**Valores comunes para `ENVIRONMENT`**:
- `development` - Desarrollo local
- `staging` - Pruebas previas a producción
- `production` - Producción

### Semilla de Desarrollo

| Variable | Descripción | Valor por Defecto |
|----------|-------------|-------------------|
| `SEED_DEV_ADMIN` | Crea usuario admin en dev si es `true` | `False` |

Notas:

- Solo aplica si `ENVIRONMENT=development`.
- Se omite si el usuario admin ya existe.

### Seguridad

| Variable | Descripción | Valor Recomendado |
|----------|-------------|-------------------|
| `SECRET_KEY` | Clave secreta para JWT | Generada aleatoriamente |
| `ALGORITHM` | Algoritmo de firma JWT | `HS256` |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | Tiempo de expiración del token (minutos) | `1440` (24 horas) |

**Generar SECRET_KEY segura:**

```bash
# Con OpenSSL
openssl rand -hex 32

# Con Python
python -c "import secrets; print(secrets.token_hex(32))"
```

**IMPORTANTE**:

- ⚠️ Nunca uses la `SECRET_KEY` de ejemplo en producción
- ⚠️ Nunca subas el archivo `.env` a control de versiones
- ✅ Añade `.env` a tu `.gitignore`
- ✅ Genera una nueva clave para cada entorno

### CORS

| Variable | Descripción | Ejemplo |
|----------|-------------|---------|
| `ALLOWED_ORIGINS` | Orígenes permitidos para CORS (separados por comas). Se normaliza a lista internamente. | `http://localhost:3000,https://app.ejemplo.com` |

**Ejemplos de configuración:**

```env
# Desarrollo local - múltiples puertos
ALLOWED_ORIGINS=http://localhost:3000,http://localhost:8080,http://localhost:4200

# Producción - dominios específicos
ALLOWED_ORIGINS=https://app.ejemplo.com,https://admin.ejemplo.com

# Permitir todos (NO RECOMENDADO en producción)
ALLOWED_ORIGINS=*
```

### Paginación

La paginación se maneja con parámetros `skip` y `limit` en los endpoints. Si se requiere centralizar valores por defecto/máximos, se pueden añadir al `Settings` en `app/core/settings.py`.

---

## Configuración por Entorno

### Desarrollo Local

```env
DEBUG=True
ENVIRONMENT=development
DATABASE_URL=sqlite:///./inventario.db
RELOAD=True
ALLOWED_ORIGINS=http://localhost:3000,http://localhost:8080
```

### Staging/Pruebas

```env
DEBUG=False
ENVIRONMENT=staging
DATABASE_URL=postgresql://user:pass@staging-db.ejemplo.com/inventario
RELOAD=False
ALLOWED_ORIGINS=https://staging.ejemplo.com
SECRET_KEY=clave_generada_aleatoriamente_para_staging
```

### Producción

```env
DEBUG=False
ENVIRONMENT=production
DATABASE_URL=postgresql://user:pass@prod-db.ejemplo.com/inventario
RELOAD=False
ALLOWED_ORIGINS=https://app.ejemplo.com,https://admin.ejemplo.com
SECRET_KEY=clave_generada_aleatoriamente_para_produccion
ACCESS_TOKEN_EXPIRE_MINUTES=60
```

**Recomendaciones para producción:**

1. ✅ Usa base de datos externa (PostgreSQL/MySQL)
2. ✅ `DEBUG=False` para evitar exponer información sensible
3. ✅ `RELOAD=False` para mejor rendimiento
4. ✅ Limita `ALLOWED_ORIGINS` a dominios específicos
5. ✅ Reduce `ACCESS_TOKEN_EXPIRE_MINUTES` según necesidad de seguridad
6. ✅ Usa HTTPS en producción

---

## Uso en la Aplicación

### Cargar Settings centralizado

```python
from app.core.settings import get_settings

settings = get_settings()
print(settings.DATABASE_URL)
print(settings.APP_NAME)
```

### Configuración de FastAPI y CORS

```python
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.core.settings import get_settings

settings = get_settings()

app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description=settings.APP_DESCRIPTION,
    debug=settings.DEBUG,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[str(o) for o in settings.ALLOWED_ORIGINS],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

### Configuración de Base de Datos (referencia)

`app/database/database.py` ya usa `settings`. Si necesitas crear un engine aparte:

```python
from sqlalchemy import create_engine
from app.core.settings import get_settings

settings = get_settings()
engine = create_engine(
    settings.DATABASE_URL,
    connect_args={"check_same_thread": False} if "sqlite" in settings.DATABASE_URL else {},
    echo=settings.DEBUG,
)
```

### Configuración de Autenticación (referencia)

Las dependencias de `app/src/auth/dependencies.py` obtienen `SECRET_KEY`, `ALGORITHM` y `ACCESS_TOKEN_EXPIRE_MINUTES` desde `settings`; no es necesario leer `.env` manualmente.

---

## Troubleshooting

### Error: "SECRET_KEY no configurada"

**Causa**: No se encontró la variable `SECRET_KEY` en el archivo `.env`.

**Solución**:

1. Verifica que existe el archivo `.env` en la raíz del proyecto
2. Genera una clave secreta: `openssl rand -hex 32`
3. Añade `SECRET_KEY=tu_clave_generada` al archivo `.env`

### Error: "Database connection failed"

**Causa**: `DATABASE_URL` incorrecta o base de datos no accesible.

**Solución**:

1. Verifica que `DATABASE_URL` tenga el formato correcto
2. Para PostgreSQL/MySQL: verifica credenciales y que el servidor esté corriendo
3. Para SQLite: verifica permisos de escritura en el directorio

### CORS Error en el Frontend

**Causa**: El origen del frontend no está en `ALLOWED_ORIGINS`.

**Solución**:

1. Añade el origen del frontend a `ALLOWED_ORIGINS`
2. Ejemplo: `ALLOWED_ORIGINS=http://localhost:3000`
3. Reinicia el servidor después de cambiar `.env`

### Variables no se cargan

**Causa**: Archivo `.env` no se carga correctamente.

**Solución**:

1. Verifica que `python-dotenv` esté instalado: `pip install python-dotenv`
2. Asegúrate de llamar `load_dotenv()` antes de acceder a variables
3. Verifica la ubicación del archivo `.env` (debe estar en la raíz)

---

## Buenas Prácticas

### Seguridad (buenas prácticas)

✅ **HACER:**

- Usar variables de entorno para datos sensibles
- Generar claves aleatorias únicas por entorno
- Añadir `.env` al `.gitignore`
- Rotar `SECRET_KEY` periódicamente en producción
- Usar HTTPS en producción

❌ **NO HACER:**

- Subir `.env` a Git/GitHub
- Usar la misma `SECRET_KEY` en todos los entornos
- Poner credenciales directamente en el código
- Usar `DEBUG=True` en producción
- Permitir `ALLOWED_ORIGINS=*` en producción

### Gestión de Configuración

✅ **HACER:**

- Crear archivo `.env.example` con valores de ejemplo (sin datos sensibles)
- Documentar cada variable en el README
- Usar valores por defecto razonables cuando sea posible
- Validar variables críticas al inicio de la aplicación

❌ **NO HACER:**

- Asumir que las variables siempre existen
- Usar valores por defecto inseguros
- Ignorar errores de configuración

### Ejemplo de .env.example

```env
# Base de datos
DATABASE_URL=sqlite:///./inventario.db

# Aplicación
APP_NAME=Sistema de Inventario
APP_VERSION=1.0.0
DEBUG=True
ENVIRONMENT=development

# Seguridad (CAMBIAR en producción)
SECRET_KEY=CAMBIAR_ESTA_CLAVE_POR_UNA_ALEATORIA
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=1440

# CORS
ALLOWED_ORIGINS=http://localhost:3000
```

---

## Dependencias Requeridas

`pydantic-settings` ya está incluido en `requirements.txt` y se usa como mecanismo principal de configuración.
