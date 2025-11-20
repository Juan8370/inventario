# 🧭 Roadmap y Recomendaciones Backend

Este documento describe la hoja de ruta para la evolución del backend del Sistema de Inventario, priorizando la robustez, seguridad y escalabilidad sin dependencias de frontend.

---

## 🗺️ Roadmap por Fases

### Fase 1: Consolidación del Dominio y Base Técnica
**Objetivo**: Asegurar que el núcleo del negocio (inventario, ventas, compras) sea sólido y la base técnica sea mantenible.

#### 🏢 Dominio
- [ ] **Ajustes de Inventario**: Endpoint para correcciones manuales (mermas, conteos) con motivo justificado.
- [ ] **Reservas de Stock**: Implementar lógica de `cantidad_reservada` para órdenes en proceso.
- [ ] **Proveedores**: Entidad completa con validación de RUC/Identificación y relación real con Compras.
- [ ] **Devoluciones**: Lógica para revertir ventas (nota de crédito) y compras (devolución a proveedor).

#### 🛠️ Técnico
- [ ] **Migraciones (Alembic)**: Implementar sistema de migraciones para control de cambios en BD (reemplazar `create_all`).
- [ ] **Refactorización de Routers**: Estandarizar respuestas y manejo de errores en todos los módulos.
- [ ] **Validaciones Avanzadas**: Constraints en BD (CHECKs) para integridad de datos (ej. `total >= 0`).

---

### Fase 2: Seguridad y Operaciones
**Objetivo**: Blindar la aplicación y facilitar su gestión en entornos productivos.

#### 🔒 Seguridad
- [ ] **Rate Limiting**: Proteger endpoints públicos (login) contra fuerza bruta.
- [ ] **Auditoría Avanzada**: Registrar cambios de estado sensibles (ej. anulación de venta) con motivo y usuario.
- [ ] **Rotación de Secretos**: Mecanismo para rotar `SECRET_KEY` sin invalidar sesiones activas inmediatamente.
- [ ] **Headers de Seguridad**: Implementar HSTS, CSP y otros headers recomendados.

#### ⚙️ Operaciones
- [ ] **Health Checks Profundos**: Endpoint `/health/deep` que verifique conexión a BD y servicios externos.
- [ ] **Graceful Shutdown**: Manejo correcto de señales (SIGTERM) para cerrar conexiones limpiamente.
- [ ] **Configuración Dinámica**: Posibilidad de recargar ciertas configuraciones sin reinicio (ej. niveles de log).

---

### Fase 3: Rendimiento y Observabilidad
**Objetivo**: Preparar el sistema para alta carga y mejorar la visibilidad del comportamiento interno.

#### 🚀 Rendimiento
- [ ] **Índices Optimizados**: Análisis de queries lentas y creación de índices compuestos.
- [ ] **Caching**: Implementar caché (Redis) para endpoints de lectura frecuente (ej. catálogo de productos).
- [ ] **Paginación Eficiente**: Estandarizar paginación por cursor para grandes volúmenes de datos.

#### 👁️ Observabilidad
- [ ] **Logging Estructurado**: Formato JSON en producción con `request_id` para trazabilidad distribuida.
- [ ] **Métricas (Prometheus)**: Exponer métricas de latencia, errores y throughput.
- [ ] **Alertas**: Definir umbrales para alertas automáticas (ej. CPU > 80%, Errores > 1%).

---

### Fase 4: Escalabilidad y Futuro
**Objetivo**: Funcionalidades avanzadas para un sistema maduro.

- [ ] **Tareas en Segundo Plano**: Procesamiento asíncrono (Celery/Arq) para reportes pesados o emails.
- [ ] **Webhooks**: Sistema de notificaciones a sistemas externos (ej. "Stock Bajo" -> Slack).
- [ ] **Multi-tenant**: Preparación para soporte de múltiples empresas en la misma instancia (si aplica).
- [ ] **API Versioning**: Estrategia `/api/v1`, `/api/v2` para evolución sin rupturas.

---

## 📝 Recomendaciones de Organización (Inmediatas)

### Estructura del Proyecto
Mantener la separación clara de responsabilidades:
- `app/routers`: Controladores de API.
- `app/src/services`: Lógica de negocio compleja (desacoplar de routers).
- `app/src/database`: Capa de persistencia.
- `app/core`: Configuración y utilidades transversales.

### Calidad de Código
- **Pre-commit hooks**: Forzar `ruff` y `black` antes de cada commit.
- **Type Hinting**: Mantener cobertura de tipos estáticos (mypy/pyright) al 100%.
- **Tests**: Exigir tests para cada nueva funcionalidad (coverage > 80%).

### Gestión de Datos
- **Seed Data**: Mantener actualizado `seed.py` y `fake_data.py` para reflejar cambios en el modelo.
- **Backups**: Estrategia de respaldo de BD (dump diario + streaming WAL si es Postgres).

---

*Última actualización: 20 de Noviembre de 2025*
