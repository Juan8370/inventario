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

---

# 🗺️ Roadmap Backend (sin Front)

Este roadmap organiza el trabajo futuro en pistas paralelas (funcional, técnica y operativa). Se estructura por fases con prioridades claras y entregables verificables solo de backend.

## 🎯 Objetivos Globales
- Robustecer el dominio: inventario confiable, trazabilidad completa y reglas claras.
- Seguridad y cumplimiento: autenticación, autorización, auditoría, configuración segura.
- Calidad y mantenibilidad: tests, migraciones, CI/CD, observabilidad.

## Fase 1 — Consolidación del Núcleo (1–2 semanas)

1) Dominio de Inventario
- Ajustes de inventario: endpoint para ajustes manuales con motivo (corrección, merma) y doble validación (rol + log obligatorio).
- Reservas de stock: campos y endpoints para reservar/liberar unidades (para futuras ventas/órdenes), afectando `cantidad_reservada` y `disponible`.
- Reportes base: bajo stock, rotación por período, kardex por producto (derivado de `Transaccion`).

2) Compras
- Proveedores (tabla y CRUD): `proveedores` con validaciones (RUC/razón social), y FK en `compras` (reemplazar `proveedor_id` int suelto por FK real vía migración Alembic).
- Validaciones numéricas: coherencia entre subtotal/impuesto/descuento/total en servidor (ya presente) + constraints en BD (CHECK cuando DB lo permita).

3) Transacciones
- Idempotencia opcional: llave externa opcional `external_id` para evitar doble inserción cuando se integren fuentes externas.
- Endpoint de re-cálculo: recomputar `Inventario` desde `Transaccion` por producto (herramienta de reparación).

4) Técnica
- Alembic productivo: migraciones versionadas; retirar auto-create en prod.
- Pre-commit (ruff/black/isort) + Pyright/Mypy en CI.
- Cobertura mínima en CI (pytest-cov) y badge opcional.

5) Observabilidad y Seguridad
- Estructurar logs de aplicación (nivel INFO/WARN/ERROR) además de logs de dominio (tabla `logs`).
- Rate limiting (a nivel de gateway o dependencia simple) para endpoints críticos.
- Revisar CORS y headers de seguridad; reforzar validación de `SECRET_KEY`/config obligatoria.

Entregables: modelos + migraciones, endpoints documentados en `docs/api.md`, tests unitarios e integración, checklist de seguridad básico.

## Fase 2 — Ventas y Flujo Comercial (2–3 semanas)

1) Ventas (cabecera + detalles)
- Registrar ventas con `DetalleVenta` y generar transacciones SALIDA automáticas (con validaciones de stock y unidad mínima).
- Estados de venta (pendiente, pagada, anulada): cambios de estado con impacto en stock (anulación revierte stock con transacción ENTRADA de ajuste).

2) Devoluciones
- Devolución de compra: ENTRADA negativa o SALIDA según política; definir `tipo_transaccion` específico "DEVOLUCION_COMPRA" si conviene.
- Devolución de venta: transacción ENTRADA con vínculo a venta y motivo.

3) Finanzas básicas (solo metadatos)
- Cuentas por pagar (cabecera de compra → estado pagado/pendiente, sin contabilidad completa).
- Cuentas por cobrar (venta → estado cobro), sin asientos contables.

4) Técnica
- Paginación y filtrado consistentes: helper común (skip/limit/sort/filter) y parámetros estandarizados.
- Versionado de API: prefijar `/api/v1` y preparar estrategia de evolución.

Entregables: endpoints de ventas/devoluciones, reglas de negocio documentadas, tests de flujo integrado (compra→stock→venta→devolución), documentación actualizada.

## Fase 3 — Integridad, Rendimiento y Escalabilidad (2–4 semanas)

1) Integridad y Consistencia
- Transacciones ACID a nivel de servicio para operaciones multi-tabla (compra con múltiples ítems, venta con detalles).
- Bloqueos/optimistic locking donde aplique (evitar oversell con contención alta).
- Tareas de reconciliación: job que compara `Inventario` vs suma de transacciones y emite alertas.

2) Rendimiento
- Índices adicionales guiados por perfiles de consulta (por fecha, producto, proveedor, estado).
- Endpoints de reporte con agregaciones (usar consultas eficientes, vistas/materializaciones si motor lo permite).

3) Observabilidad
- Estructura de logs con trazas (correlation/request id) y métricas básicas (tiempo de respuesta por endpoint, errores por tipo).
- Exportación a un sink (opcional): files/ELK/OTel (configurable por entorno).

4) Seguridad avanzada
- Hardening de dependencias y escaneo SCA en CI.
- Auditoría ampliada: registrar cambios de estados sensibles (ventas, devoluciones, ajustes) con detalle de usuario/razón.

Entregables: perfiles de rendimiento, migraciones de índices, tareas de reconciliación, panel simple de métricas (endpoint `/stats/extended`).

## Fase 4 — Integraciones y Automatización (3–6 semanas)

1) Integraciones
- Conectores CSV/Excel para importación/exportación de productos y transacciones (backend-only).
- Webhooks o colas (opcional) para notificar eventos (compra creada, stock bajo).

2) Automatización
- Jobs programados (APScheduler/Cron) para: alertas de bajo stock, expiración de lotes, conciliación nocturna.

3) Multi-tenant ligero (opcional)
- `empresa_id`/scope por tenant si se requiere aislar datos; políticas de acceso por empresa.

Entregables: endpoints/importadores, tareas programadas, documentación de eventos.

## Estándares Transversales
- Documentación: mantener `docs/api.md` y `docs/database.md` actualizados por PR.
- Backward compatibility: no romper contratos; si es necesario, versionar endpoint.
- Testing: comenzar específico → flujos completos; repetir suite completa en CI antes de merge.
- Migrations-first: todo cambio de modelo con Alembic y scripts revisados.

## Riesgos y Mitigaciones
- Inconsistencias de inventario: endpoint de recalculo, jobs de reconciliación y transacciones atómicas.
- Carrera de stock en alta concurrencia: locking/estrategia idempotente y validaciones a nivel SQL.
- Fugas de configuración: validar settings obligatorios al arranque y secretos fuera del repo.

---

Siguientes pasos sugeridos: implementar Proveedores (Fase 1) con migración Alembic, endpoint de ajustes de inventario con motivos y tests; luego preparar versionado `/api/v1` y helpers de filtrado/paginación para estandarizar los siguientes módulos.
