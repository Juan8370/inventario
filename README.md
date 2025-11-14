# 📦 Sistema de Inventario

Un sistema completo de gestión de inventario desarrollado con FastAPI, SQLAlchemy y Pydantic.

## 🚀 Características

- ✅ **Gestión de Usuarios** - Sistema completo de autenticación y autorización
- ✅ **Catálogo de Productos** - Control completo de productos con tipos y estados
- ✅ **Control de Inventario** - Seguimiento en tiempo real de stock y ubicaciones
- ✅ **Sistema de Ventas** - Registro de ventas con detalles completos
- ✅ **Gestión de Empresas** - Administración de empresas y empleados
- ✅ **Validaciones Robustas** - Tipado fuerte con Pydantic
- ✅ **Tests Completos** - Cobertura completa de funcionalidades

## 🏗️ Arquitectura

```
inventario/
├── app/
│   ├── database/
│   │   ├── models.py      # Modelos SQLAlchemy
│   │   └── schemas.py     # Esquemas Pydantic
│   ├── src/              # Lógica de aplicación
│   └── main.py           # Punto de entrada
├── docs/
│   └── database.md       # Documentación completa
├── test/
│   └── test_database.py  # Tests de base de datos
└── requirements.txt      # Dependencias
```

## 🔧 Instalación

1. **Clonar el repositorio**
```bash
git clone <repository-url>
cd inventario
```

2. **Crear entorno virtual**
```bash
python -m venv .venv
.venv\Scripts\activate  # Windows
# source .venv/bin/activate  # Linux/Mac
```

3. **Instalar dependencias**
```bash
pip install -r requirements.txt
# Para desarrollo: pip install -r requirements-dev.txt
```

4. **Ejecutar tests**
```bash
pytest test/ -v
```

## 🗄️ Base de Datos

El sistema utiliza SQLAlchemy con soporte para múltiples bases de datos:
- SQLite (desarrollo)
- PostgreSQL (producción recomendada)
- MySQL (alternativa)

### Tablas Principales:
- `usuarios` - Gestión de usuarios del sistema
- `empresas` - Información de empresas
- `empleados` - Gestión de recursos humanos  
- `productos` - Catálogo de productos
- `inventario` - Control de stock
- `ventas` - Registro de transacciones
- `detalle_ventas` - Detalles de cada venta

Para más detalles, consultar [documentación de base de datos](docs/database.md).

## 🧪 Testing

```bash
# Ejecutar todos los tests
pytest

# Tests con cobertura
pytest --cov=app

# Tests específicos
pytest test/test_database.py -v
```

## 📚 Documentación

- [Setup](docs/setup.md) - Puesta en marcha y ejecución
- [Entorno](docs/env.md) - Variables de entorno (.env)
- [API](docs/api.md) - Endpoints, códigos y payloads
- [CRUD Genérico](docs/crud.md) - Uso de `CRUDBase`
- [Testing](docs/testing.md) - Cómo ejecutar y qué cubren los tests
- [Arquitectura](docs/architecture.md) - Estructura y flujo de la app
- [Base de Datos](docs/database.md) - Esquema y relaciones
- API interactiva - Disponible en `/docs` cuando el servidor está corriendo

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
