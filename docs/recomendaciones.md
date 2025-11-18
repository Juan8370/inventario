# 🧭 Recomendaciones de Organización y Mejora

Este documento propone mejoras incrementales para escalar y mantener el proyecto de forma más ordenada, segura y sostenible. Están priorizadas y pensadas para adoptarse por fases.

---

## ✅ Cambios Prioritarios (rápidos, alto impacto)

- **Modularizar routers**: mover los endpoints de `app/main.py` a módulos bajo `app/routers/` (`auth.py`, `productos.py`, `empresas.py`, `usuarios.py`) y usar `include_router` en `main.py`.
- **Configuración centralizada**: crear `app/core/settings.py` con `pydantic-settings` para cargar/validar `.env` en una sola clase `Settings`. Evita `os.getenv` disperso.
- **Logging unificado**: reemplazar `print` por `logging` con configuración por entorno (niveles, formato, JSON opcional en producción).
- **Semilla de datos controlada**: mantener el admin de desarrollo, pero gatearlo con `SEED_DEV_ADMIN=true` además de `ENVIRONMENT=development`.

---

## 🧱 Cambios Estructurales (mediano plazo)

- **Módulos por dominio**: renombrar `app/src/auth` a `app/auth` y considerar `app/modules/<dominio>/*` para agrupar `routers`, `schemas`, `service`, `repository` por funcionalidad.
- **Separar schemas del ORM**: mover `app/src/database/schemas.py` a `app/src/schemas/` o por dominio (`app/src/productos/schemas.py`). Mantiene desacoplada la capa API de la persistencia.
- **Capa de servicios**: formalizar servicios por dominio (por ejemplo `app/productos/service.py`) para concentrar reglas de negocio fuera de los routers.
- **Utilidades de paginación/filtros**: extraer validaciones y parámetros comunes (paginación, orden, búsqueda) a `app/common/pagination.py` y `app/common/filters.py`.

---

## 🗃️ Migraciones y Base de Datos

- **Alembic**: añadir migraciones en lugar de crear tablas en runtime en producción. Mantener auto-create solo para desarrollo/test.
  - Inicialización sugerida:
    ```powershell
    alembic init migrations
    # Configurar sqlalchemy.url en alembic.ini y target_metadata en env.py
    alembic revision --autogenerate -m "init"
    alembic upgrade head
    ```
- **Índices y constraints**: revisar que reglas de negocio críticas estén respaldadas en BD (UNIQUE, CHECK, FKs), no solo en Pydantic.

---

## 🔒 Calidad, Seguridad y DX

- **Pre-commit**: integrar `ruff`, `black`, `isort` y formateo automático.
- **Tipos estáticos**: activar `pyright`/`mypy` para detectar errores antes de runtime.
- **Manejo de errores**: centralizar `HTTPException` y errores de validación con handlers en `app/core/exception_handlers.py` para respuestas consistentes.
- **Headers y CORS**: documentar y validar `ALLOWED_ORIGINS`; en prod evitar `*`. Añadir tests mínimos para CORS.
- **Secrets**: validar presencia de `SECRET_KEY` al boot y fallar temprano en prod si falta.

---

## 🔁 Tests y CI

- **Test matrix**: mantener la BD en memoria para unit/integration; añadir smoke tests de arranque.
- **Cobertura**: publicar reporte de `pytest-cov` en CI y umbral mínimo.
- **Pipelines**: job de `lint + tests` como requisito antes de merge.

---

## 🧩 Estructura Propuesta (ejemplo)

```
app/
  core/
    settings.py          # pydantic-settings
    logging.py           # config de logging
    exception_handlers.py
  routers/
    auth.py
    productos.py
    empresas.py
    usuarios.py
  auth/
    jwt.py
    password.py
    crud.py
    service.py
    dependencies.py
  database/
    database.py
    models.py
    crud.py
    init_data.py
  productos/
    service.py
    schemas.py
  common/
    pagination.py
    filters.py
```

---

## 🗺️ Plan de Adopción por Fases

1) **Fase 1 (1–2 días)**
- Crear `Settings` y reemplazar `os.getenv`.
- Configurar `logging` y handlers de excepciones.
- Extraer routers a `app/routers/*`.

2) **Fase 2 (2–3 días)**
- Integrar Alembic y generar la migración inicial.
- Separar schemas por dominio.
- Añadir utilidades de paginación/filtros y aplicarlas en endpoints.

3) **Fase 3 (2–4 días)**
- Pre-commit (ruff/black/isort) y pyright en CI.
- Reorganizar módulos por dominio (`app/modules/*`) si procede.
- Tests adicionales de CORS, errores y logging.

---

## 📌 Notas Operativas

- Mantener `create_tables()` para tests y dev; deshabilitar en prod y depender de migraciones.
- La siembra del usuario admin solo en dev y bajo flag `SEED_DEV_ADMIN`.
- Documentar decisiones en `docs/architecture.md` (si se reintroduce) o anexar a `setup.md`.

---

## 🧪 Checklist Rápido

- [ ] Routers modularizados
- [ ] Settings centralizado con validación
- [ ] Logging configurado por entorno
- [ ] Alembic en producción
- [ ] Schemas separados del ORM
- [ ] Handlers de errores globales
- [ ] Pre-commit + tipos en CI
- [ ] Utilidades de paginación/filtros
