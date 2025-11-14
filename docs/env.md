# ⚙️ Variables de Entorno (.env)

La aplicación se configura mediante variables de entorno cargadas con `python-dotenv`.

## Archivo .env

Copia desde `.env.example` y ajusta valores:

```env
# Base de datos
DATABASE_URL=sqlite:///./inventario.db
# Ejemplos:
# postgresql://usuario:password@localhost/inventario
# mysql+pymysql://usuario:password@localhost/inventario

# App
APP_NAME=Sistema de Inventario
APP_VERSION=1.0.0
APP_DESCRIPTION=API para gestión de inventario
DEBUG=True
ENVIRONMENT=development

# Servidor
HOST=0.0.0.0
PORT=8000
RELOAD=True

# Seguridad
SECRET_KEY=tu_clave_secreta_super_segura_cambiala_en_produccion
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30

# CORS
ALLOWED_ORIGINS=http://localhost:3000,http://localhost:8080

# Paginación
DEFAULT_PAGE_SIZE=10
MAX_PAGE_SIZE=100
```

## Notas

- En SQLite, la ruta `sqlite:///./inventario.db` crea el archivo junto al `run.py`.
- En producción, cambia `DEBUG=False`, configura `SECRET_KEY` seguro y usa una BD externa (PostgreSQL recomendado).
- `ALLOWED_ORIGINS` es una lista separada por comas para CORS.
