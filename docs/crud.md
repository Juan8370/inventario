# 🧩 CRUD Genérico (`CRUDBase`)

Archivo: `app/database/crud.py`

Provee operaciones CRUD reutilizables para cualquier modelo SQLAlchemy.

## Uso básico

```python
from app.database.crud import CRUDBase
from app.database.models import Producto
from app.database import schemas

crud_producto = CRUDBase[Producto, schemas.ProductoCreate, schemas.ProductoUpdate](Producto)

# Crear
nuevo = crud_producto.create(db, obj_in=schemas.ProductoCreate(...))

# Obtener
p = crud_producto.get(db, id=1)

# Actualizar
p2 = crud_producto.update(db, db_obj=p, obj_in={"nombre": "Nuevo"})

# Eliminar
crud_producto.delete(db, id=1)
```

## Métodos disponibles

- `get(db, id)`
- `get_or_404(db, id)` → lanza 404 si no existe
- `get_multi(db, skip=0, limit=100, filters=None, order_by=None)`
- `count(db, filters=None)`
- `create(db, obj_in)`
- `update(db, db_obj, obj_in)`
- `delete(db, id)`
- `get_by_field(db, field, value)`
- `exists(db, id)`
- `bulk_create(db, objs_in)`
- `bulk_delete(db, ids)`
- `search(db, search_fields, search_term, skip=0, limit=100)`

## Filtros y búsqueda

```python
# Filtros simples
crud_producto.get_multi(db, filters={"estado_producto_id": 1})

# Filtros avanzados
crud_producto.get_multi(db, filters={
  "precio_venta": {"gte": 100, "lte": 500},
  "nombre": {"like": "Laptop"}
})

# Búsqueda por texto
crud_producto.search(db, ["nombre", "codigo", "marca"], "Laptop")
```
