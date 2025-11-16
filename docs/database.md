# 📊 Base de Datos - Sistema de Inventario

## Arquitectura General

Este sistema utiliza **SQLAlchemy** como ORM y **Pydantic v2** para validación de datos, implementando un diseño relacional robusto con separación clara entre:

- **Tablas de Configuración**: Tipos y estados para clasificación
- **Tablas Principales**: Entidades de negocio core (Productos, Empresas, Usuarios, Ventas)
- **Tablas de Transacciones**: Operaciones del sistema (Inventario, DetalleVenta)

### Configuración de Base de Datos

**Archivo**: `app/database/database.py`

- Motor: SQLAlchemy con soporte para SQLite, PostgreSQL, MySQL
- Sesión: `SessionLocal` con autocommit/autoflush deshabilitado
- Dependency injection: `get_db()` para FastAPI
- Creación automática de tablas en startup (solo desarrollo/test; en producción usar migraciones)

```python
from app.database.database import engine, SessionLocal, get_db

# Usar en endpoints
@app.get("/ejemplo")
def endpoint(db: Session = Depends(get_db)):
    return db.query(Producto).all()
```

---

## Índice de Contenidos

1. [Tablas de Configuración](#tablas-de-configuración)
2. [Tablas Principales](#tablas-principales)
3. [Relaciones](#relaciones-entre-tablas)
4. [Validaciones](#validaciones-y-restricciones)
5. [Índices y Rendimiento](#índices-y-rendimiento)
6. [Esquemas Pydantic](#esquemas-pydantic)
7. [CRUD Genérico](#crud-genérico)
8. [Casos de Uso](#casos-de-uso-típicos)

---

## 🔧 Tablas de Configuración

### TipoUsuario
**Propósito**: Define los roles y permisos de usuarios del sistema.

| Campo | Tipo | Descripción | Restricciones |
|-------|------|-------------|---------------|
| `id` | Integer | Clave primaria | PRIMARY KEY, AUTO_INCREMENT |
| `nombre` | String(50) | Nombre del tipo | UNIQUE, NOT NULL |
| `descripcion` | Text | Descripción detallada | NULLABLE |
| `activo` | Boolean | Estado del tipo | DEFAULT TRUE |
| `fecha_creacion` | DateTime | Timestamp de creación | DEFAULT CURRENT_TIMESTAMP |

**Ejemplos**: Administrador, Vendedor, Supervisor, Almacenero

### EstadoUsuario
**Propósito**: Control del estado de cuenta de usuarios.

| Campo | Tipo | Descripción | Restricciones |
|-------|------|-------------|---------------|
| `id` | Integer | Clave primaria | PRIMARY KEY, AUTO_INCREMENT |
| `nombre` | String(50) | Nombre del estado | UNIQUE, NOT NULL |
| `descripcion` | Text | Descripción del estado | NULLABLE |
| `activo` | Boolean | Estado activo | DEFAULT TRUE |
| `fecha_creacion` | DateTime | Timestamp de creación | DEFAULT CURRENT_TIMESTAMP |

**Ejemplos**: Activo, Inactivo, Suspendido, Pendiente

### TipoProducto
**Propósito**: Categorización de productos para organización y reportes.

| Campo | Tipo | Descripción | Restricciones |
|-------|------|-------------|---------------|
| `id` | Integer | Clave primaria | PRIMARY KEY, AUTO_INCREMENT |
| `nombre` | String(100) | Nombre del tipo | UNIQUE, NOT NULL |
| `descripcion` | Text | Descripción del tipo | NULLABLE |
| `activo` | Boolean | Estado activo | DEFAULT TRUE |
| `fecha_creacion` | DateTime | Timestamp de creación | DEFAULT CURRENT_TIMESTAMP |

**Ejemplos**: Electrónicos, Ropa, Alimentos, Medicamentos, Herramientas

### EstadoProducto
**Propósito**: Control del ciclo de vida de productos.

| Campo | Tipo | Descripción | Restricciones |
|-------|------|-------------|---------------|
| `id` | Integer | Clave primaria | PRIMARY KEY, AUTO_INCREMENT |
| `nombre` | String(50) | Nombre del estado | UNIQUE, NOT NULL |
| `descripcion` | Text | Descripción del estado | NULLABLE |
| `activo` | Boolean | Estado activo | DEFAULT TRUE |
| `fecha_creacion` | DateTime | Timestamp de creación | DEFAULT CURRENT_TIMESTAMP |

**Ejemplos**: Disponible, Agotado, Descontinuado, En Revisión

### EstadoVenta
**Propósito**: Seguimiento del proceso de ventas.

| Campo | Tipo | Descripción | Restricciones |
|-------|------|-------------|---------------|
| `id` | Integer | Clave primaria | PRIMARY KEY, AUTO_INCREMENT |
| `nombre` | String(50) | Nombre del estado | UNIQUE, NOT NULL |
| `descripcion` | Text | Descripción del estado | NULLABLE |
| `activo` | Boolean | Estado activo | DEFAULT TRUE |
| `fecha_creacion` | DateTime | Timestamp de creación | DEFAULT CURRENT_TIMESTAMP |

**Ejemplos**: Pendiente, Procesada, Entregada, Cancelada, Devuelta

### TipoEmpresa
**Propósito**: Clasificación de empresas cliente o proveedoras.

| Campo | Tipo | Descripción | Restricciones |
|-------|------|-------------|---------------|
| `id` | Integer | Clave primaria | PRIMARY KEY, AUTO_INCREMENT |
| `nombre` | String(100) | Nombre del tipo | UNIQUE, NOT NULL |
| `descripcion` | Text | Descripción del tipo | NULLABLE |
| `activo` | Boolean | Estado activo | DEFAULT TRUE |
| `fecha_creacion` | DateTime | Timestamp de creación | DEFAULT CURRENT_TIMESTAMP |

**Ejemplos**: Proveedor, Cliente, Distribuidor, Socio Comercial

### EstadoEmpresa
**Propósito**: Estado de la relación comercial con empresas.

| Campo | Tipo | Descripción | Restricciones |
|-------|------|-------------|---------------|
| `id` | Integer | Clave primaria | PRIMARY KEY, AUTO_INCREMENT |
| `nombre` | String(50) | Nombre del estado | UNIQUE, NOT NULL |
| `descripcion` | Text | Descripción del estado | NULLABLE |
| `activo` | Boolean | Estado activo | DEFAULT TRUE |
| `fecha_creacion` | DateTime | Timestamp de creación | DEFAULT CURRENT_TIMESTAMP |

**Ejemplos**: Activo, Suspendido, Bloqueado, En Evaluación

### EstadoEmpleado
**Propósito**: Control del estado laboral de empleados.

| Campo | Tipo | Descripción | Restricciones |
|-------|------|-------------|---------------|
| `id` | Integer | Clave primaria | PRIMARY KEY, AUTO_INCREMENT |
| `nombre` | String(50) | Nombre del estado | UNIQUE, NOT NULL |
| `descripcion` | Text | Descripción del estado | NULLABLE |
| `activo` | Boolean | Estado activo | DEFAULT TRUE |
| `fecha_creacion` | DateTime | Timestamp de creación | DEFAULT CURRENT_TIMESTAMP |

**Ejemplos**: Activo, Licencia, Vacaciones, Retirado, Suspendido

---

## 🏢 Tablas Principales

### Empresa
**Propósito**: Información de empresas del ecosistema comercial.

| Campo | Tipo | Descripción | Restricciones |
|-------|------|-------------|---------------|
| `id` | Integer | Clave primaria | PRIMARY KEY, AUTO_INCREMENT |
| `nombre` | String(200) | Razón social | NOT NULL |
| `ruc` | String(20) | Registro único | UNIQUE, NOT NULL |
| `direccion` | Text | Dirección fiscal | NULLABLE |
| `telefono` | String(20) | Teléfono principal | NULLABLE |
| `email` | String(100) | Email corporativo | NULLABLE |
| `contacto_principal` | String(200) | Persona de contacto | NULLABLE |
| `tipo_empresa_id` | Integer | FK a TipoEmpresa | FOREIGN KEY, NOT NULL |
| `estado_empresa_id` | Integer | FK a EstadoEmpresa | FOREIGN KEY, NOT NULL |
| `fecha_creacion` | DateTime | Timestamp de creación | DEFAULT CURRENT_TIMESTAMP |
| `fecha_actualizacion` | DateTime | Última actualización | ON UPDATE CURRENT_TIMESTAMP |

**Índices**: 
- `idx_empresa_ruc` (ruc)
- `idx_empresa_nombre` (nombre)

### Usuario
**Propósito**: Usuarios del sistema con autenticación y autorización.

| Campo | Tipo | Descripción | Restricciones |
|-------|------|-------------|---------------|
| `id` | Integer | Clave primaria | PRIMARY KEY, AUTO_INCREMENT |
| `username` | String(50) | Nombre de usuario | UNIQUE, NOT NULL, INDEX |
| `email` | String(100) | Email único | UNIQUE, NOT NULL, INDEX |
| `password_hash` | String(255) | Hash de contraseña | NOT NULL |
| `nombre` | String(100) | Nombre real | NOT NULL |
| `apellido` | String(100) | Apellido | NOT NULL |
| `telefono` | String(20) | Teléfono personal | NULLABLE |
| `fecha_ultimo_acceso` | DateTime | Último login | NULLABLE |
| `empresa_id` | Integer | FK a Empresa | FOREIGN KEY, NULLABLE |
| `tipo_usuario_id` | Integer | FK a TipoUsuario | FOREIGN KEY, NOT NULL |
| `estado_usuario_id` | Integer | FK a EstadoUsuario | FOREIGN KEY, NOT NULL |
| `fecha_creacion` | DateTime | Timestamp de creación | DEFAULT CURRENT_TIMESTAMP |
| `fecha_actualizacion` | DateTime | Última actualización | ON UPDATE CURRENT_TIMESTAMP |

**Índices**:
- `idx_usuario_username` (username)
- `idx_usuario_email` (email)

### Empleado
**Propósito**: Gestión de recursos humanos y nómina.

| Campo | Tipo | Descripción | Restricciones |
|-------|------|-------------|---------------|
| `id` | Integer | Clave primaria | PRIMARY KEY, AUTO_INCREMENT |
| `codigo_empleado` | String(20) | Código único | UNIQUE, NOT NULL |
| `nombre` | String(100) | Nombre completo | NOT NULL |
| `apellido` | String(100) | Apellido | NOT NULL |
| `documento_identidad` | String(20) | Cédula/DNI | UNIQUE, NOT NULL |
| `telefono` | String(20) | Teléfono personal | NULLABLE |
| `email` | String(100) | Email personal | NULLABLE |
| `direccion` | Text | Dirección residencial | NULLABLE |
| `cargo` | String(100) | Posición laboral | NULLABLE |
| `salario` | Decimal(10,2) | Salario mensual | NULLABLE |
| `fecha_ingreso` | DateTime | Fecha de contratación | NULLABLE |
| `fecha_salida` | DateTime | Fecha de retiro | NULLABLE |
| `empresa_id` | Integer | FK a Empresa | FOREIGN KEY, NOT NULL |
| `estado_empleado_id` | Integer | FK a EstadoEmpleado | FOREIGN KEY, NOT NULL |
| `fecha_creacion` | DateTime | Timestamp de creación | DEFAULT CURRENT_TIMESTAMP |
| `fecha_actualizacion` | DateTime | Última actualización | ON UPDATE CURRENT_TIMESTAMP |

**Índices**:
- `idx_empleado_codigo` (codigo_empleado)
- `idx_empleado_documento` (documento_identidad)

### Producto
**Propósito**: Catálogo maestro de productos comercializables.

| Campo | Tipo | Descripción | Restricciones |
|-------|------|-------------|---------------|
| `id` | Integer | Clave primaria | PRIMARY KEY, AUTO_INCREMENT |
| `codigo` | String(50) | SKU/Código único | UNIQUE, NOT NULL, INDEX |
| `nombre` | String(200) | Nombre comercial | NOT NULL, INDEX |
| `descripcion` | Text | Descripción detallada | NULLABLE |
| `marca` | String(100) | Marca comercial | NULLABLE |
| `modelo` | String(100) | Modelo específico | NULLABLE |
| `precio_compra` | Decimal(10,2) | Costo de adquisición | NULLABLE |
| `precio_venta` | Decimal(10,2) | Precio de venta | NULLABLE |
| `stock_minimo` | Integer | Umbral de reorden | DEFAULT 0 |
| `unidad_medida` | String(20) | Unidad (pza, kg, lt) | NULLABLE |
| `tipo_producto_id` | Integer | FK a TipoProducto | FOREIGN KEY, NOT NULL |
| `estado_producto_id` | Integer | FK a EstadoProducto | FOREIGN KEY, NOT NULL |
| `fecha_creacion` | DateTime | Timestamp de creación | DEFAULT CURRENT_TIMESTAMP |
| `fecha_actualizacion` | DateTime | Última actualización | ON UPDATE CURRENT_TIMESTAMP |

**Índices**:
- `idx_producto_codigo` (codigo)
- `idx_producto_nombre` (nombre)

### Inventario
**Propósito**: Control de stock y ubicaciones físicas.

| Campo | Tipo | Descripción | Restricciones |
|-------|------|-------------|---------------|
| `id` | Integer | Clave primaria | PRIMARY KEY, AUTO_INCREMENT |
| `producto_id` | Integer | FK a Producto | FOREIGN KEY, NOT NULL |
| `cantidad_actual` | Integer | Stock real | NOT NULL, DEFAULT 0 |
| `cantidad_reservada` | Integer | Stock comprometido | DEFAULT 0 |
| `cantidad_disponible` | Integer | Stock libre | DEFAULT 0 |
| `ubicacion` | String(100) | Ubicación física | NULLABLE |
| `lote` | String(50) | Número de lote | NULLABLE |
| `fecha_vencimiento` | DateTime | Fecha de caducidad | NULLABLE |
| `fecha_ultima_entrada` | DateTime | Última recepción | NULLABLE |
| `fecha_ultima_salida` | DateTime | Última salida | NULLABLE |
| `fecha_actualizacion` | DateTime | Última actualización | ON UPDATE CURRENT_TIMESTAMP |

**Reglas de Negocio**:
- `cantidad_disponible = cantidad_actual - cantidad_reservada`
- `cantidad_reservada ≤ cantidad_actual`

### Venta
**Propósito**: Registro de transacciones de venta.

| Campo | Tipo | Descripción | Restricciones |
|-------|------|-------------|---------------|
| `id` | Integer | Clave primaria | PRIMARY KEY, AUTO_INCREMENT |
| `numero_venta` | String(50) | Número de factura | UNIQUE, NOT NULL, INDEX |
| `cliente_nombre` | String(200) | Nombre del cliente | NOT NULL |
| `cliente_documento` | String(20) | Documento del cliente | NULLABLE |
| `cliente_telefono` | String(20) | Teléfono del cliente | NULLABLE |
| `cliente_email` | String(100) | Email del cliente | NULLABLE |
| `cliente_direccion` | Text | Dirección de entrega | NULLABLE |
| `subtotal` | Decimal(10,2) | Suma sin impuestos | NOT NULL |
| `impuesto` | Decimal(10,2) | Impuestos aplicados | DEFAULT 0 |
| `descuento` | Decimal(10,2) | Descuentos aplicados | DEFAULT 0 |
| `total` | Decimal(10,2) | Monto final | NOT NULL |
| `fecha_venta` | DateTime | Fecha de transacción | DEFAULT CURRENT_TIMESTAMP |
| `usuario_id` | Integer | FK a Usuario | FOREIGN KEY, NOT NULL |
| `estado_venta_id` | Integer | FK a EstadoVenta | FOREIGN KEY, NOT NULL |
| `observaciones` | Text | Notas adicionales | NULLABLE |
| `fecha_creacion` | DateTime | Timestamp de creación | DEFAULT CURRENT_TIMESTAMP |
| `fecha_actualizacion` | DateTime | Última actualización | ON UPDATE CURRENT_TIMESTAMP |

**Reglas de Negocio**:
- `total = subtotal + impuesto - descuento`
- `total > 0`

**Índices**:
- `idx_venta_numero` (numero_venta)
- `idx_venta_fecha` (fecha_venta)
- `idx_venta_cliente` (cliente_nombre)

### DetalleVenta
**Propósito**: Líneas individuales de cada venta.

| Campo | Tipo | Descripción | Restricciones |
|-------|------|-------------|---------------|
| `id` | Integer | Clave primaria | PRIMARY KEY, AUTO_INCREMENT |
| `venta_id` | Integer | FK a Venta | FOREIGN KEY, NOT NULL |
| `producto_id` | Integer | FK a Producto | FOREIGN KEY, NOT NULL |
| `cantidad` | Integer | Unidades vendidas | NOT NULL |
| `precio_unitario` | Decimal(10,2) | Precio por unidad | NOT NULL |
| `descuento_unitario` | Decimal(10,2) | Descuento por unidad | DEFAULT 0 |
| `subtotal` | Decimal(10,2) | Total de la línea | NOT NULL |
| `fecha_creacion` | DateTime | Timestamp de creación | DEFAULT CURRENT_TIMESTAMP |

**Reglas de Negocio**:
- `subtotal = (precio_unitario - descuento_unitario) * cantidad`
- `cantidad > 0`

---

## 🔗 Relaciones Entre Tablas

### Diagrama de Relaciones

```
Empresa (1) ──── (N) Usuario
   │                │
   │                └── (1) ──── (N) Venta
   │                                │
   └── (N) Empleado                 └── (1) ──── (N) DetalleVenta
                                                       │
TipoUsuario (1) ──── (N) Usuario                      │
EstadoUsuario (1) ──── (N) Usuario                    │
                                                       │
TipoProducto (1) ──── (N) Producto ──── (1) ──────────┘
EstadoProducto (1) ──── (N) Producto                  
                            │
                            └── (1) ──── (N) Inventario

TipoEmpresa (1) ──── (N) Empresa
EstadoEmpresa (1) ──── (N) Empresa

EstadoEmpleado (1) ──── (N) Empleado

EstadoVenta (1) ──── (N) Venta
```

### Relaciones Detalladas

#### Usuario ↔ Empresa
- **Tipo**: Many-to-One (N:1)
- **Descripción**: Un usuario pertenece a una empresa, una empresa puede tener múltiples usuarios
- **FK**: `usuarios.empresa_id → empresas.id`

#### Venta ↔ Usuario
- **Tipo**: Many-to-One (N:1)
- **Descripción**: Una venta es registrada por un usuario, un usuario puede registrar múltiples ventas
- **FK**: `ventas.usuario_id → usuarios.id`

#### DetalleVenta ↔ Venta
- **Tipo**: Many-to-One (N:1)
- **Descripción**: Un detalle pertenece a una venta, una venta tiene múltiples detalles
- **FK**: `detalle_ventas.venta_id → ventas.id`

#### DetalleVenta ↔ Producto
- **Tipo**: Many-to-One (N:1)
- **Descripción**: Un detalle referencia un producto, un producto puede estar en múltiples detalles
- **FK**: `detalle_ventas.producto_id → productos.id`

#### Inventario ↔ Producto
- **Tipo**: One-to-Many (1:N)
- **Descripción**: Un producto puede tener múltiples registros de inventario (por ubicación, lote, etc.)
- **FK**: `inventario.producto_id → productos.id`

---

## ✅ Validaciones y Restricciones

### Validaciones a Nivel de Base de Datos

#### Restricciones UNIQUE
- `usuarios.username` - Nombres de usuario únicos
- `usuarios.email` - Emails únicos por usuario
- `empresas.ruc` - RUC único por empresa
- `empleados.codigo_empleado` - Códigos únicos
- `empleados.documento_identidad` - Documentos únicos
- `productos.codigo` - SKUs únicos
- `ventas.numero_venta` - Números de venta únicos

#### Restricciones NOT NULL
- Campos obligatorios marcados como NOT NULL
- Claves foráneas obligatorias para integridad referencial

#### Restricciones CHECK (implementables)
```sql
-- Validar que cantidad_reservada <= cantidad_actual
ALTER TABLE inventario ADD CONSTRAINT chk_inventario_cantidades 
CHECK (cantidad_reservada <= cantidad_actual);

-- Validar que precio_venta >= precio_compra (si ambos están presentes)
ALTER TABLE productos ADD CONSTRAINT chk_producto_precios 
CHECK (precio_compra IS NULL OR precio_venta IS NULL OR precio_venta >= precio_compra);

-- Validar que el total de venta sea positivo
ALTER TABLE ventas ADD CONSTRAINT chk_venta_total 
CHECK (total > 0);
```

### Validaciones con Pydantic

#### Validaciones de Formato
- **Email**: Formato válido usando `EmailStr`
- **Teléfono**: Patrón regex `^[\+0-9\-\s\(\)]+$`
- **RUC**: Patrón regex `^[0-9-]+$`
- **Códigos**: Patrón regex `^[A-Za-z0-9\-_]+$`
- **Username**: Patrón regex `^[a-zA-Z0-9_]+$`

#### Validaciones de Longitud
- **Nombres**: Min 1, Max según tabla
- **Descripciones**: Max 500-1000 caracteres
- **Códigos**: Min 1, Max 50 caracteres

#### Validaciones de Rango
- **Decimales**: `ge=0` (mayor o igual a cero)
- **Enteros**: `gt=0` (mayor a cero) para IDs
- **Stock**: `ge=0` (no negativo)

#### Validaciones Complejas (Root Validators)
- **Precios**: Precio venta ≥ precio compra
- **Stock**: cantidad_disponible = cantidad_actual - cantidad_reservada
- **Totales**: Cálculo automático de subtotales y totales
- **Contraseñas**: Mínimo 8 caracteres, debe incluir letras y números

---

## 🚀 Índices y Rendimiento

### Índices Principales

#### Índices de Clave Primaria
- Automáticos en todos los campos `id`

#### Índices Únicos
- `usuarios.username`
- `usuarios.email`
- `empresas.ruc`
- `empleados.codigo_empleado`
- `empleados.documento_identidad`
- `productos.codigo`
- `ventas.numero_venta`

#### Índices de Búsqueda
- `productos.nombre` - Búsquedas de productos
- `empresas.nombre` - Búsquedas de empresas
- `ventas.fecha_venta` - Reportes por fecha
- `ventas.cliente_nombre` - Búsquedas de clientes

#### Índices de Clave Foránea
SQLAlchemy crea automáticamente índices para mejorar JOINs:
- Todas las relaciones `*_id` tienen índices implícitos

### Estrategias de Optimización

#### Consultas Frecuentes
```sql
-- Búsqueda de productos por código (INDEXED)
SELECT * FROM productos WHERE codigo = 'PROD001';

-- Inventario actual de productos (JOIN optimizado)
SELECT p.nombre, i.cantidad_actual 
FROM productos p 
JOIN inventario i ON p.id = i.producto_id;

-- Ventas por usuario y fecha (INDEXED)
SELECT * FROM ventas 
WHERE usuario_id = 1 
  AND fecha_venta >= '2024-01-01';
```

#### Paginación Eficiente
```python
# Uso de LIMIT/OFFSET con ORDER BY para paginación
query = session.query(Producto)\
    .order_by(Producto.nombre)\
    .limit(20)\
    .offset(page * 20)
```

---

## 📝 Esquemas Pydantic

### Estructura de Esquemas

Cada entidad tiene 4 tipos de esquemas:

#### 1. BaseSchema
```python
class ProductoBase(BaseModel):
    # Campos comunes para create/update
    nombre: str = Field(..., min_length=1, max_length=200)
    # ... otros campos
```

#### 2. CreateSchema  
```python
class ProductoCreate(ProductoBase):
    # Hereda de Base + campos obligatorios para creación
    pass
```

#### 3. UpdateSchema
```python
class ProductoUpdate(BaseModel):
    # Todos los campos opcionales para actualizaciones parciales
    nombre: Optional[str] = Field(None, min_length=1, max_length=200)
    # ... otros campos opcionales
```

#### 4. ResponseSchema
```python
class Producto(ProductoBase):
    # Hereda de Base + campos de respuesta (id, fechas, relaciones)
    id: int
    fecha_creacion: datetime
    tipo_producto: Optional[TipoProducto] = None
    
    class Config:
        from_attributes = True  # Compatibilidad con SQLAlchemy
```

### Validaciones Implementadas

#### Validators Simples
```python
@validator('codigo')
def validar_codigo(cls, v):
    if not re.match(r'^[A-Za-z0-9\-_]+$', v):
        raise ValueError('Formato de código inválido')
    return v
```

#### Root Validators
```python
@root_validator
def validar_precios(cls, values):
    precio_compra = values.get('precio_compra')
    precio_venta = values.get('precio_venta')
    
    if precio_compra and precio_venta and precio_venta < precio_compra:
        raise ValueError('Precio de venta menor al de compra')
    return values
```

---

## CRUD Genérico

### Descripción

**Archivo**: `app/database/crud.py`

`CRUDBase` provee operaciones CRUD reutilizables para cualquier modelo SQLAlchemy, reduciendo la duplicación de código.

### Uso Básico

```python
from app.database.crud import CRUDBase
from app.database.models import Producto
from app.database import schemas

# Instanciar CRUD para Producto
crud_producto = CRUDBase[Producto, schemas.ProductoCreate, schemas.ProductoUpdate](Producto)

# Crear
nuevo = crud_producto.create(db, obj_in=schemas.ProductoCreate(...))

# Obtener
producto = crud_producto.get(db, id=1)

# Actualizar
producto_actualizado = crud_producto.update(db, db_obj=producto, obj_in={"nombre": "Nuevo Nombre"})

# Eliminar
crud_producto.delete(db, id=1)
```

### Métodos Disponibles

| Método | Descripción |
|--------|-------------|
| `get(db, id)` | Obtiene registro por ID |
| `get_or_404(db, id)` | Obtiene o lanza 404 si no existe |
| `get_multi(db, skip=0, limit=100, filters=None, order_by=None)` | Lista con paginación y filtros |
| `count(db, filters=None)` | Cuenta registros con filtros opcionales |
| `create(db, obj_in)` | Crea nuevo registro |
| `update(db, db_obj, obj_in)` | Actualiza registro existente |
| `delete(db, id)` | Elimina registro por ID |
| `get_by_field(db, field, value)` | Busca por campo específico |
| `exists(db, id)` | Verifica existencia por ID |
| `bulk_create(db, objs_in)` | Crea múltiples registros |
| `bulk_delete(db, ids)` | Elimina múltiples registros |
| `search(db, search_fields, search_term, skip=0, limit=100)` | Búsqueda por texto en múltiples campos |

### Filtros y Búsqueda

```python
# Filtros simples
productos = crud_producto.get_multi(db, filters={"estado_producto_id": 1})

# Filtros avanzados
productos = crud_producto.get_multi(db, filters={
    "precio_venta": {"gte": 100, "lte": 500},
    "nombre": {"like": "Laptop"}
})

# Búsqueda por texto en múltiples campos
resultados = crud_producto.search(
    db,
    search_fields=["nombre", "codigo", "marca"],
    search_term="Laptop",
    skip=0,
    limit=20
)
```

---

## Casos de Uso Típicos

### 1. Registro de Nueva Venta

```python
# 1. Crear venta
venta_data = VentaCreate(
    numero_venta="V-2024-001",
    cliente_nombre="Juan Pérez",
    subtotal=100.00,
    total=118.00,
    usuario_id=1,
    estado_venta_id=1,
    detalle_ventas=[
        DetalleVentaCreate(
            producto_id=1,
            cantidad=2,
            precio_unitario=50.00,
            subtotal=100.00
        )
    ]
)

# 2. Validar stock disponible
inventario = session.query(Inventario)\
    .filter(Inventario.producto_id == 1).first()

if inventario.cantidad_disponible < 2:
    raise ValueError("Stock insuficiente")

# 3. Actualizar inventario
inventario.cantidad_actual -= 2
inventario.cantidad_disponible -= 2
inventario.fecha_ultima_salida = datetime.utcnow()
```

### 2. Control de Stock Mínimo

```python
# Productos con stock bajo el mínimo
productos_agotandose = session.query(Producto)\
    .join(Inventario)\
    .filter(Inventario.cantidad_actual <= Producto.stock_minimo)\
    .all()

for producto in productos_agotandose:
    # Generar alerta o orden de compra automática
    enviar_alerta_stock_bajo(producto)
```

### 3. Reporte de Ventas por Período

```python
# Ventas del mes actual
from sqlalchemy import func, extract

ventas_mes = session.query(
    func.count(Venta.id).label('cantidad_ventas'),
    func.sum(Venta.total).label('total_vendido')
).filter(
    extract('month', Venta.fecha_venta) == datetime.now().month,
    extract('year', Venta.fecha_venta) == datetime.now().year
).first()
```

### 4. Gestión de Usuarios y Permisos

```python
# Usuarios activos por empresa
usuarios_activos = session.query(Usuario)\
    .join(EstadoUsuario)\
    .filter(
        Usuario.empresa_id == empresa_id,
        EstadoUsuario.nombre == 'Activo'
    )\
    .all()

# Validar permisos por tipo de usuario
if usuario.tipo_usuario.nombre in ['Administrador', 'Supervisor']:
    # Permitir operación
    pass
else:
    raise PermissionError("Usuario sin permisos")
```

### 5. Auditoría y Trazabilidad

```python
# Historial de movimientos de un producto
movimientos = session.query(DetalleVenta)\
    .join(Venta)\
    .filter(DetalleVenta.producto_id == producto_id)\
    .order_by(Venta.fecha_venta.desc())\
    .all()

# Último usuario que modificó un registro
ultimo_cambio = producto.fecha_actualizacion
usuario_modificacion = session.query(Usuario)\
    .join(Venta)\
    .filter(Venta.fecha_actualizacion == ultimo_cambio)\
    .first()
```

---

## 🔒 Consideraciones de Seguridad

### Autenticación y Autorización
- Contraseñas hasheadas (nunca en texto plano)
- Validación de roles por `tipo_usuario_id`
- Control de acceso por empresa (`empresa_id`)

### Integridad de Datos
- Transacciones ACID para operaciones críticas
- Validaciones tanto en Pydantic como en base de datos
- Claves foráneas con restricciones de integridad referencial

### Auditoría
- Campos `fecha_creacion` y `fecha_actualizacion` en todas las tablas
- Registro de `fecha_ultimo_acceso` en usuarios
- Trazabilidad de cambios por `usuario_id` en ventas

---

## 🚀 Próximos Pasos y Mejoras

### Funcionalidades Adicionales
1. **Historial de Cambios**: Tabla de auditoría para tracking completo
2. **Compras**: Módulo de órdenes de compra y recepción
3. **Reportes Avanzados**: Dashboard con métricas de negocio
4. **API REST**: Endpoints completos con FastAPI
5. **Notificaciones**: Sistema de alertas automáticas

### Optimizaciones
1. **Particionado**: Para tablas de alto volumen (ventas, inventario)
2. **Índices Compuestos**: Para consultas específicas frecuentes  
3. **Vistas Materializadas**: Para reportes complejos
4. **Cache**: Implementar Redis para consultas frecuentes

### Integrations
1. **ERP Integration**: Conexión con sistemas externos
2. **E-commerce**: Sincronización con tiendas online
3. **Contabilidad**: Integración con sistemas contables
4. **BI Tools**: Conectores para herramientas de análisis

---

## 📞 Soporte y Documentación

Para más información sobre la implementación, consultar:
- `app/database/models.py` - Modelos SQLAlchemy
- `app/database/schemas.py` - Esquemas Pydantic  
- `docs/api/` - Documentación de endpoints (próximamente)
- `tests/` - Casos de prueba y ejemplos de uso

---

*Documentación actualizada el 16 de Noviembre de 2025*
