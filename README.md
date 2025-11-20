# 📦 Sistema de Inventario

Sistema de gestión de inventario con FastAPI, SQLAlchemy y Pydantic. Se aplicó la Fase 1 de mejoras: configuración centralizada, logging unificado, manejo global de errores y routers modularizados. Además, se incorporó el módulo de Transacciones e Inventario automático, y el módulo de Compras.

## 🚀 Características

- ✅ Autenticación JWT y autorización por rol (admin/usuario)
- ✅ Productos, Empresas y Usuarios con CRUD y validaciones
- ✅ **Sistema de Logs inmutables** con auditoría completa y trazabilidad
- ✅ **Transacciones (ENTRADA/SALIDA)** con actualización automática de `Inventario`
- ✅ **Compras** como cabecera; items se registran como transacciones ENTRADA
- ✅ Configuración centralizada con `pydantic-settings`
- ✅ Logging por entorno (legible en dev, JSON en prod)
- ✅ Handlers globales de errores (`HTTPException`, validación)
- ✅ Routers modularizados: `system`, `auth`, `productos`, `empresas`, `usuarios`, `stats`, `logs`, `transacciones`, `compras`
- ✅ Suite de tests (109) pasando (incluye pruebas de transacciones y compras)

## 🏗️ Arquitectura (resumen)

```
inventario/
├── app/
│   ├── src/
│       ├── core/
│       │   ├── settings.py            # Configuración centralizada (pydantic-settings)
│       │   ├── logging.py             # Configuración de logging
│       │   └── exception_handlers.py  # Manejo global de errores
│       ├── routers/
│       │   ├── system.py   # /, /health, /db/info
│       │   ├── auth.py     # /auth/*
│       │   ├── productos.py
│       │   ├── empresas.py
│       │   ├── usuarios.py
│       │   ├── stats.py    # /stats
│       │   ├── logs.py     # /logs - Sistema de auditoría
│       │   ├── transacciones.py # /transacciones - Movimientos de inventario
│       │   └── compras.py       # /compras - Cabecera + items como ENTRADA
│       ├── database/
│       │   ├── database.py
│       │   ├── models.py
│       │   ├── schemas.py
│       │   ├── crud.py
│       │   ├── init_data.py
│       │   └── log_helper.py  # Helpers para logs
│       ├─── auth/       # jwt, password, crud, service, dependencies
│       │   
│       └── main.py
├── docs/
│   ├── setup.md
│   ├── api.md
│   ├── config.md
│   ├── database.md
│   └── recomendaciones.md
├── test/
│   ├── test_api_endpoints.py
│   ├── test_auth.py
│   ├── test_database.py
│   └── test_logs.py  # 26 tests para logs
├── .env.example
├── run.py
└── requirements.txt
```

## 🔧 Puesta en marcha rápida

### Clonar el repositorio

```powershell
git clone <repository-url>
cd inventario
```

### Crear entorno virtual

```powershell
py -m venv .venv
.\.venv\Scripts\Activate.ps1
```

### Instalar dependencias y arrancar

```powershell
pip install -r requirements.txt
# Desarrollo: pip install -r requirements-dev.txt
Copy-Item .env.example .env

# (Opcional) Poblar base de datos con datos de prueba
python seed.py

# Iniciar servidor
py run.py
```

API: <http://localhost:8000> • Docs: <http://localhost:8000/docs>

 

## 🗄️ Base de datos (resumen)

- Desarrollo/Test: crea tablas automáticamente al iniciar.
- Producción: no auto-crea tablas; se recomienda usar migraciones (Alembic).
- Soporte: SQLite, PostgreSQL, MySQL.
- **Nuevas tablas**: `tipos_log`, `logs` (inmutables), `tipos_transaccion`, `transacciones`, `compras`.

Detalles en `docs/database.md`.

### 📝 Sistema de Logs

- **Inmutabilidad**: Los logs NO pueden modificarse ni eliminarse (HTTP 403).
- **5 tipos predefinidos**: ERROR, WARNING, INFO, LOGIN, SIGNUP.
- **Visibilidad controlada**: Los usuarios ven solo sus logs, los admins ven todos.
- **Helpers**: `log_error()`, `log_warning()`, `log_info()`, `log_login()`, `log_signup()`.
- **Logs automáticos**: Login, creación de productos, usuarios, empresas, y más.

Ver documentación completa en `docs/database.md` sección "Sistema de Logs y Auditoría" y `docs/api.md` sección "Endpoints de Logs".

### 🔄 Transacciones e Inventario

- Crear una transacción ENTRADA/SALIDA actualiza automáticamente el `Inventario` del producto.
- Para SALIDA se valida que el stock sea suficiente (suma transacciones).
- Endpoints clave: ver `docs/api.md` sección "Endpoints de Transacciones".

### 🛒 Compras

- Compras es una cabecera; los items se agregan en batch y se registran como transacciones ENTRADA con `compra_id`.
- El inventario se crea si no existe y se incrementa por cada ítem.
- Endpoints clave: ver `docs/api.md` sección "Endpoints de Compras".

## 🧪 Tests

- Estado actual: **109 tests pasando**.

```powershell
pytest -q
# Tests específicos de logs
pytest test/test_logs.py -v
```

## 📚 Documentación

- `docs/setup.md` - Instalación y ejecución
- `docs/config.md` - Configuración y variables de entorno
- `docs/api.md` - Endpoints y auth
- `docs/database.md` - Esquema y relaciones
- `docs/recomendaciones.md` - Roadmap y mejoras

API interactiva: `/docs` (Swagger) y `/redoc`.

## 🤝 Contribuciones

1. Fork el proyecto
2. Crea una rama feature (`git checkout -b feature/AmazingFeature`)
3. Commit tus cambios (`git commit -m 'Add AmazingFeature'`)
4. Push a la rama (`git push origin feature/AmazingFeature`)
5. Abre un Pull Request

## 📄 Licencia

Este proyecto está bajo la Licencia MIT. Ver `LICENSE` para más detalles.

---

Desarrollado con ❤️ usando Python y FastAPI
