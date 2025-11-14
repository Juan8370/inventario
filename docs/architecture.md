# 🧱 Arquitectura del Proyecto

## Estructura de carpetas

```text
  main.py                 # FastAPI app, CORS, endpoints, wiring
  database/
    models.py             # SQLAlchemy models
    schemas.py            # Pydantic v2 schemas (field/model validators)
    database.py           # Engine, SessionLocal, get_db, create/drop tables
    crud.py               # CRUDBase genérico (reutilizable)
run.py                    # Arranque simple con uvicorn

docs/                    # Documentación del proyecto

test/
  test_database.py        # Estructura y relaciones BD
  test_endpoints.py       # Tests de API y flujos
  conftest.py             # Config global de pytest
```

## Puntos clave

- FastAPI con CORS configurable via env (`ALLOWED_ORIGINS`).
- Creación automática de tablas al `startup`.
- `CRUDBase` para reducir repetición de lógica de acceso a datos.
- Validaciones Pydantic v2: `@field_validator` y `@model_validator`.
- Serialización de decimales de `Producto` como números para consistencia en respuestas.
- Tests con BD aislada y `dependency_overrides` para `get_db`.

## Flujo de una petición típica

1. Request HTTP → `app.main` (endpoint)
2. Dependencia `get_db` inyecta una sesión de BD
3. Lógica `CRUDBase` ejecuta consulta/operación
4. Retorno de modelo → esquema Pydantic (`from_attributes=True`)
5. Respuesta JSON (status code configurado por endpoint)

## Variables de entorno usadas

- `APP_NAME`, `APP_DESCRIPTION`, `APP_VERSION`, `DEBUG`
- `DATABASE_URL`
- `ALLOWED_ORIGINS`
- Ver `docs/env.md` para detalles
