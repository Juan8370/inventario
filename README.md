# 📦 Sistema de Inventario

Sistema de gestión de inventario con FastAPI, SQLAlchemy y Pydantic. Se aplicó la Fase 1 de mejoras: configuración centralizada, logging unificado, manejo global de errores y routers modularizados.

## 🚀 Características

- ✅ Autenticación JWT y autorización por rol (admin/usuario)
- ✅ Productos, Empresas y Usuarios con CRUD y validaciones
- ✅ Configuración centralizada con `pydantic-settings`
- ✅ Logging por entorno (legible en dev, JSON en prod)
- ✅ Handlers globales de errores (`HTTPException`, validación)
- ✅ Routers modularizados: `system`, `auth`, `productos`, `empresas`, `usuarios`, `stats`
- ✅ Suite de tests (61) pasando tras refactor

## 🏗️ Arquitectura (resumen)

```
inventario/
├── app/
│   ├── core/
│   │   ├── settings.py            # Configuración centralizada (pydantic-settings)
│   │   ├── logging.py             # Configuración de logging
│   │   └── exception_handlers.py  # Manejo global de errores
│   ├── routers/
│   │   ├── system.py   # /, /health, /db/info
│   │   ├── auth.py     # /auth/*
│   │   ├── productos.py
│   │   ├── empresas.py
│   │   ├── usuarios.py
│   │   └── stats.py    # /stats
│   ├── database/
│   │   ├── database.py
│   │   ├── models.py
│   │   ├── schemas.py
│   │   ├── crud.py
│   │   └── init_data.py
│   ├── src/
│   │   └── auth/       # jwt, password, crud, service, dependencies
│   └── main.py
├── docs/
│   ├── setup.md
│   ├── api.md
│   ├── config.md
│   ├── database.md
│   └── recomendaciones.md
├── test/
│   ├── test_api_endpoints.py
│   ├── test_auth.py
│   └── test_database.py
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
py run.py
```

API: <http://localhost:8000> • Docs: <http://localhost:8000/docs>

 

## 🗄️ Base de datos (resumen)

- Desarrollo/Test: crea tablas automáticamente al iniciar.
- Producción: no auto-crea tablas; se recomienda usar migraciones (Alembic).
- Soporte: SQLite, PostgreSQL, MySQL.

Detalles en `docs/database.md`.

## 🧪 Tests

- Estado actual: 61 tests pasando tras la refactorización de Fase 1.

```powershell
pytest -q
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
