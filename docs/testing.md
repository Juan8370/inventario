# 🧪 Pruebas Automatizadas

Los tests viven en `test/` y cubren estructura de BD y endpoints.

## Ejecutar tests

```powershell
pytest -v
# o archivo específico
pytest test/test_endpoints.py -v
```

## Estructura

- `test_database.py`: Estructura de tablas, FKs, constraints y operaciones básicas.
- `test_endpoints.py`: Salud, Productos (CRUD + búsqueda + paginación), Empresas, Validaciones e Integración.
- `conftest.py`: Configuración global de PyTest.

## Base de datos de pruebas

- Se usa SQLite (`test_inventario.db`) con un `engine` propio.
- `get_db` se sobreescribe para aislar la BD de pruebas.
- En teardown: `Base.metadata.drop_all()` + `engine.dispose()` y borrado de archivo (evita locks en Windows).

## Notas importantes

- Pydantic v2: validaciones con `@field_validator` y `@model_validator`.
- Paginación: `skip >= 0`, `limit >= 1` devuelven 422 cuando son inválidos.
- Serialización: precios de productos se devuelven como números (no strings).
