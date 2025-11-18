from typing import Generic, TypeVar, Type, Optional, List, Any, Dict
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_
from fastapi import HTTPException
from pydantic import BaseModel
from app.src.database.models import Base

# Tipos genéricos para el CRUD
ModelType = TypeVar("ModelType", bound=Base)
CreateSchemaType = TypeVar("CreateSchemaType", bound=BaseModel)
UpdateSchemaType = TypeVar("UpdateSchemaType", bound=BaseModel)


class CRUDBase(Generic[ModelType, CreateSchemaType, UpdateSchemaType]):
    """
    Clase genérica CRUD con operaciones básicas de:
    - Create (Crear)
    - Read (Leer)
    - Update (Actualizar)
    - Delete (Eliminar)
    """

    def __init__(self, model: Type[ModelType]):
        """
        Inicializa el CRUD con el modelo de SQLAlchemy.
        
        Args:
            model: Modelo de SQLAlchemy
        """
        self.model = model

    def get(self, db: Session, id: Any) -> Optional[ModelType]:
        """
        Obtiene un registro por ID.
        
        Args:
            db: Sesión de base de datos
            id: ID del registro
            
        Returns:
            Registro encontrado o None
        """
        return db.query(self.model).filter(self.model.id == id).first()

    def get_or_404(self, db: Session, id: Any) -> ModelType:
        """
        Obtiene un registro por ID o lanza una excepción 404.
        
        Args:
            db: Sesión de base de datos
            id: ID del registro
            
        Returns:
            Registro encontrado
            
        Raises:
            HTTPException: Si no se encuentra el registro
        """
        obj = self.get(db, id)
        if not obj:
            raise HTTPException(
                status_code=404,
                detail=f"{self.model.__name__} con id {id} no encontrado"
            )
        return obj

    def get_multi(
        self,
        db: Session,
        *,
        skip: int = 0,
        limit: int = 100,
        filters: Optional[Dict[str, Any]] = None,
        order_by: Optional[str] = None
    ) -> List[ModelType]:
        """
        Obtiene múltiples registros con paginación y filtros opcionales.
        
        Args:
            db: Sesión de base de datos
            skip: Número de registros a saltar
            limit: Límite de registros a retornar
            filters: Diccionario de filtros {campo: valor}
            order_by: Campo por el cual ordenar
            
        Returns:
            Lista de registros
        """
        query = db.query(self.model)
        
        # Aplicar filtros si existen
        if filters:
            filter_conditions = []
            for key, value in filters.items():
                if hasattr(self.model, key):
                    if isinstance(value, list):
                        # Filtro IN para listas
                        filter_conditions.append(getattr(self.model, key).in_(value))
                    elif isinstance(value, dict):
                        # Filtros complejos como >= , <=, etc.
                        for op, val in value.items():
                            if op == "gte":
                                filter_conditions.append(getattr(self.model, key) >= val)
                            elif op == "lte":
                                filter_conditions.append(getattr(self.model, key) <= val)
                            elif op == "gt":
                                filter_conditions.append(getattr(self.model, key) > val)
                            elif op == "lt":
                                filter_conditions.append(getattr(self.model, key) < val)
                            elif op == "like":
                                filter_conditions.append(getattr(self.model, key).like(f"%{val}%"))
                    else:
                        # Filtro de igualdad
                        filter_conditions.append(getattr(self.model, key) == value)
            
            if filter_conditions:
                query = query.filter(and_(*filter_conditions))
        
        # Aplicar ordenamiento
        if order_by and hasattr(self.model, order_by):
            query = query.order_by(getattr(self.model, order_by))
        
        return query.offset(skip).limit(limit).all()

    def count(self, db: Session, filters: Optional[Dict[str, Any]] = None) -> int:
        """
        Cuenta el número de registros que cumplen con los filtros.
        
        Args:
            db: Sesión de base de datos
            filters: Diccionario de filtros {campo: valor}
            
        Returns:
            Número de registros
        """
        query = db.query(self.model)
        
        if filters:
            filter_conditions = []
            for key, value in filters.items():
                if hasattr(self.model, key):
                    if isinstance(value, list):
                        filter_conditions.append(getattr(self.model, key).in_(value))
                    else:
                        filter_conditions.append(getattr(self.model, key) == value)
            
            if filter_conditions:
                query = query.filter(and_(*filter_conditions))
        
        return query.count()

    def create(self, db: Session, *, obj_in: CreateSchemaType | Dict[str, Any]) -> ModelType:
        """
        Crea un nuevo registro.
        
        Args:
            db: Sesión de base de datos
            obj_in: Esquema Pydantic con los datos o diccionario
            
        Returns:
            Registro creado
        """
        if isinstance(obj_in, dict):
            obj_in_data = obj_in
        else:
            obj_in_data = obj_in.dict() if hasattr(obj_in, 'dict') else obj_in.model_dump()
        db_obj = self.model(**obj_in_data)
        db.add(db_obj)
        db.commit()
        db.refresh(db_obj)
        return db_obj

    def update(
        self,
        db: Session,
        *,
        db_obj: ModelType,
        obj_in: UpdateSchemaType | Dict[str, Any]
    ) -> ModelType:
        """
        Actualiza un registro existente.
        
        Args:
            db: Sesión de base de datos
            db_obj: Objeto de base de datos a actualizar
            obj_in: Esquema Pydantic o diccionario con los datos a actualizar
            
        Returns:
            Registro actualizado
        """
        obj_data = db_obj.__dict__
        
        if isinstance(obj_in, dict):
            update_data = obj_in
        else:
            update_data = obj_in.dict(exclude_unset=True) if hasattr(obj_in, 'dict') else obj_in.model_dump(exclude_unset=True)
        
        for field in obj_data:
            if field in update_data:
                setattr(db_obj, field, update_data[field])
        
        db.add(db_obj)
        db.commit()
        db.refresh(db_obj)
        return db_obj

    def delete(self, db: Session, *, id: int) -> ModelType:
        """
        Elimina un registro por ID.
        
        Args:
            db: Sesión de base de datos
            id: ID del registro a eliminar
            
        Returns:
            Registro eliminado
            
        Raises:
            HTTPException: Si no se encuentra el registro
        """
        obj = self.get_or_404(db, id)
        db.delete(obj)
        db.commit()
        return obj

    def get_by_field(
        self,
        db: Session,
        field: str,
        value: Any
    ) -> Optional[ModelType]:
        """
        Obtiene un registro por un campo específico.
        
        Args:
            db: Sesión de base de datos
            field: Nombre del campo
            value: Valor a buscar
            
        Returns:
            Registro encontrado o None
        """
        if not hasattr(self.model, field):
            raise ValueError(f"El modelo {self.model.__name__} no tiene el campo {field}")
        
        return db.query(self.model).filter(getattr(self.model, field) == value).first()

    def exists(self, db: Session, id: int) -> bool:
        """
        Verifica si existe un registro con el ID dado.
        
        Args:
            db: Sesión de base de datos
            id: ID del registro
            
        Returns:
            True si existe, False en caso contrario
        """
        return db.query(self.model).filter(self.model.id == id).first() is not None

    def bulk_create(self, db: Session, *, objs_in: List[CreateSchemaType]) -> List[ModelType]:
        """
        Crea múltiples registros en una sola transacción.
        
        Args:
            db: Sesión de base de datos
            objs_in: Lista de esquemas Pydantic con los datos
            
        Returns:
            Lista de registros creados
        """
        db_objs = []
        for obj_in in objs_in:
            obj_in_data = obj_in.dict() if hasattr(obj_in, 'dict') else obj_in.model_dump()
            db_obj = self.model(**obj_in_data)
            db_objs.append(db_obj)
        
        db.add_all(db_objs)
        db.commit()
        
        for db_obj in db_objs:
            db.refresh(db_obj)
        
        return db_objs

    def bulk_delete(self, db: Session, *, ids: List[int]) -> int:
        """
        Elimina múltiples registros por sus IDs.
        
        Args:
            db: Sesión de base de datos
            ids: Lista de IDs a eliminar
            
        Returns:
            Número de registros eliminados
        """
        count = db.query(self.model).filter(self.model.id.in_(ids)).delete(synchronize_session=False)
        db.commit()
        return count

    def search(
        self,
        db: Session,
        *,
        search_fields: List[str],
        search_term: str,
        skip: int = 0,
        limit: int = 100
    ) -> List[ModelType]:
        """
        Busca registros en múltiples campos usando LIKE.
        
        Args:
            db: Sesión de base de datos
            search_fields: Lista de campos en los que buscar
            search_term: Término a buscar
            skip: Número de registros a saltar
            limit: Límite de registros a retornar
            
        Returns:
            Lista de registros encontrados
        """
        query = db.query(self.model)
        
        if search_term:
            search_conditions = []
            for field in search_fields:
                if hasattr(self.model, field):
                    search_conditions.append(
                        getattr(self.model, field).like(f"%{search_term}%")
                    )
            
            if search_conditions:
                query = query.filter(or_(*search_conditions))
        
        return query.offset(skip).limit(limit).all()


class CRUDLog(Generic[ModelType, CreateSchemaType, UpdateSchemaType]):
    """
    Clase CRUD especial para Logs - INMUTABLE
    Solo permite crear y leer, NO actualizar ni eliminar
    """

    def __init__(self, model: Type[ModelType]):
        self.model = model

    def create(self, db: Session, *, obj_in: CreateSchemaType) -> ModelType:
        """
        Crea un nuevo log (INMUTABLE - no se puede modificar después).
        
        Args:
            db: Sesión de base de datos
            obj_in: Esquema Pydantic con los datos del log
            
        Returns:
            Log creado
        """
        obj_in_data = obj_in.dict() if hasattr(obj_in, 'dict') else obj_in.model_dump()
        db_obj = self.model(**obj_in_data)
        db.add(db_obj)
        db.commit()
        db.refresh(db_obj)
        return db_obj

    def get(self, db: Session, id: Any) -> Optional[ModelType]:
        """
        Obtiene un log por ID.
        
        Args:
            db: Sesión de base de datos
            id: ID del log
            
        Returns:
            Log encontrado o None
        """
        return db.query(self.model).filter(self.model.id == id).first()

    def get_multi(
        self,
        db: Session,
        *,
        skip: int = 0,
        limit: int = 100,
        filters: Optional[Dict[str, Any]] = None,
        order_by: str = "fecha"
    ) -> List[ModelType]:
        """
        Obtiene múltiples logs con paginación y filtros.
        
        Args:
            db: Sesión de base de datos
            skip: Número de registros a saltar
            limit: Límite de registros a retornar
            filters: Diccionario de filtros {campo: valor}
            order_by: Campo por el cual ordenar (default: fecha descendente)
            
        Returns:
            Lista de logs
        """
        from app.src.database.models import Log
        query = db.query(self.model)
        
        # Aplicar filtros
        if filters:
            filter_conditions = []
            for key, value in filters.items():
                if hasattr(self.model, key):
                    if isinstance(value, list):
                        filter_conditions.append(getattr(self.model, key).in_(value))
                    elif isinstance(value, dict):
                        for op, val in value.items():
                            if op == "gte":
                                filter_conditions.append(getattr(self.model, key) >= val)
                            elif op == "lte":
                                filter_conditions.append(getattr(self.model, key) <= val)
                    else:
                        filter_conditions.append(getattr(self.model, key) == value)
            
            if filter_conditions:
                query = query.filter(and_(*filter_conditions))
        
        # Ordenar por fecha descendente por defecto
        if hasattr(self.model, order_by):
            query = query.order_by(getattr(self.model, order_by).desc())
        
        return query.offset(skip).limit(limit).all()

    def count(self, db: Session, filters: Optional[Dict[str, Any]] = None) -> int:
        """
        Cuenta el número de logs que cumplen con los filtros.
        
        Args:
            db: Sesión de base de datos
            filters: Diccionario de filtros
            
        Returns:
            Número de logs
        """
        query = db.query(self.model)
        
        if filters:
            filter_conditions = []
            for key, value in filters.items():
                if hasattr(self.model, key):
                    if isinstance(value, list):
                        filter_conditions.append(getattr(self.model, key).in_(value))
                    else:
                        filter_conditions.append(getattr(self.model, key) == value)
            
            if filter_conditions:
                query = query.filter(and_(*filter_conditions))
        
        return query.count()

    def get_by_usuario(
        self,
        db: Session,
        usuario_id: int,
        *,
        skip: int = 0,
        limit: int = 100
    ) -> List[ModelType]:
        """
        Obtiene logs de un usuario específico.
        
        Args:
            db: Sesión de base de datos
            usuario_id: ID del usuario
            skip: Número de registros a saltar
            limit: Límite de registros
            
        Returns:
            Lista de logs del usuario
        """
        return self.get_multi(
            db,
            skip=skip,
            limit=limit,
            filters={"usuario_id": usuario_id, "usuario_tipo": "USUARIO"}
        )

    def get_system_logs(
        self,
        db: Session,
        *,
        skip: int = 0,
        limit: int = 100
    ) -> List[ModelType]:
        """
        Obtiene logs del sistema (no visibles para usuarios normales).
        
        Args:
            db: Sesión de base de datos
            skip: Número de registros a saltar
            limit: Límite de registros
            
        Returns:
            Lista de logs del sistema
        """
        return self.get_multi(
            db,
            skip=skip,
            limit=limit,
            filters={"usuario_tipo": "SYSTEM"}
        )

    def get_by_tipo(
        self,
        db: Session,
        tipo_log_id: int,
        *,
        skip: int = 0,
        limit: int = 100
    ) -> List[ModelType]:
        """
        Obtiene logs por tipo (ERROR, WARNING, INFO, LOGIN, SIGNUP).
        
        Args:
            db: Sesión de base de datos
            tipo_log_id: ID del tipo de log
            skip: Número de registros a saltar
            limit: Límite de registros
            
        Returns:
            Lista de logs del tipo especificado
        """
        return self.get_multi(
            db,
            skip=skip,
            limit=limit,
            filters={"tipo_log_id": tipo_log_id}
        )

    def update(self, *args, **kwargs):
        """Logs son INMUTABLES - no se pueden actualizar"""
        raise HTTPException(
            status_code=403,
            detail="Los logs son inmutables y no pueden ser modificados"
        )

    def delete(self, *args, **kwargs):
        """Logs son INMUTABLES - no se pueden eliminar"""
        raise HTTPException(
            status_code=403,
            detail="Los logs son inmutables y no pueden ser eliminados"
        )


# Instancias de CRUD para modelos
from app.src.database import models, schemas

# CRUD para tipos y estados
crud_tipo_log = CRUDBase[models.TipoLog, schemas.TipoLogCreate, schemas.TipoLogCreate](models.TipoLog)

# CRUD para Log (inmutable)
crud_log = CRUDLog[models.Log, schemas.LogCreate, None](models.Log)

# CRUD para productos
crud_producto = CRUDBase[models.Producto, schemas.ProductoCreate, schemas.ProductoUpdate](models.Producto)
crud_compra = CRUDBase[models.Compra, schemas.CompraCreate, schemas.CompraCreate](models.Compra)


class CRUDTransaccion(CRUDBase[ModelType, CreateSchemaType, UpdateSchemaType]):
    """
    CRUD específico para transacciones de inventario
    Incluye métodos especiales para consultas por producto y cálculo de stock
    """
    
    def get_by_producto(
        self,
        db: Session,
        producto_id: int,
        skip: int = 0,
        limit: int = 100
    ) -> List[ModelType]:
        """
        Obtiene todas las transacciones de un producto específico
        
        Args:
            db: Sesión de base de datos
            producto_id: ID del producto
            skip: Cantidad de registros a saltar (paginación)
            limit: Cantidad máxima de registros a retornar
        
        Returns:
            Lista de transacciones del producto
        """
        return (
            db.query(self.model)
            .filter(self.model.producto_id == producto_id)
            .order_by(self.model.fecha.desc())
            .offset(skip)
            .limit(limit)
            .all()
        )
    
    def get_entradas(
        self,
        db: Session,
        producto_id: Optional[int] = None,
        skip: int = 0,
        limit: int = 100
    ) -> List[ModelType]:
        """
        Obtiene las transacciones de tipo ENTRADA
        
        Args:
            db: Sesión de base de datos
            producto_id: ID del producto (opcional, filtra por producto)
            skip: Cantidad de registros a saltar
            limit: Cantidad máxima de registros a retornar
        
        Returns:
            Lista de transacciones de entrada
        """
        query = db.query(self.model).join(models.TipoTransaccion).filter(
            models.TipoTransaccion.nombre == "ENTRADA"
        )
        
        if producto_id:
            query = query.filter(self.model.producto_id == producto_id)
        
        return (
            query
            .order_by(self.model.fecha.desc())
            .offset(skip)
            .limit(limit)
            .all()
        )
    
    def get_salidas(
        self,
        db: Session,
        producto_id: Optional[int] = None,
        skip: int = 0,
        limit: int = 100
    ) -> List[ModelType]:
        """
        Obtiene las transacciones de tipo SALIDA
        
        Args:
            db: Sesión de base de datos
            producto_id: ID del producto (opcional, filtra por producto)
            skip: Cantidad de registros a saltar
            limit: Cantidad máxima de registros a retornar
        
        Returns:
            Lista de transacciones de salida
        """
        query = db.query(self.model).join(models.TipoTransaccion).filter(
            models.TipoTransaccion.nombre == "SALIDA"
        )
        
        if producto_id:
            query = query.filter(self.model.producto_id == producto_id)
        
        return (
            query
            .order_by(self.model.fecha.desc())
            .offset(skip)
            .limit(limit)
            .all()
        )
    
    def calcular_stock_actual(self, db: Session, producto_id: int) -> float:
        """
        Calcula el stock actual de un producto basado en sus transacciones
        
        Fórmula: ENTRADAS - SALIDAS
        
        Args:
            db: Sesión de base de datos
            producto_id: ID del producto
        
        Returns:
            Stock actual (puede ser negativo si hay más salidas que entradas)
        """
        from sqlalchemy import func
        
        # Calcular total de entradas
        entradas = (
            db.query(func.sum(self.model.cantidad))
            .join(models.TipoTransaccion)
            .filter(
                and_(
                    self.model.producto_id == producto_id,
                    models.TipoTransaccion.nombre == "ENTRADA"
                )
            )
            .scalar() or 0
        )
        
        # Calcular total de salidas
        salidas = (
            db.query(func.sum(self.model.cantidad))
            .join(models.TipoTransaccion)
            .filter(
                and_(
                    self.model.producto_id == producto_id,
                    models.TipoTransaccion.nombre == "SALIDA"
                )
            )
            .scalar() or 0
        )
        
        return float(entradas) - float(salidas)
    
    def get_productos_bajo_stock(
        self,
        db: Session,
        limite_stock: int = 10
    ) -> List[Dict[str, Any]]:
        """
        Obtiene productos cuyo stock actual está por debajo del límite
        
        Args:
            db: Sesión de base de datos
            limite_stock: Stock mínimo considerado "bajo"
        
        Returns:
            Lista de diccionarios con producto_id, nombre y stock_actual
        """
        from sqlalchemy import func
        
        # Subconsulta para calcular stock por producto
        productos = db.query(models.Producto).all()
        productos_bajo_stock = []
        
        for producto in productos:
            stock = self.calcular_stock_actual(db, producto.id)
            if stock < limite_stock:
                productos_bajo_stock.append({
                    "producto_id": producto.id,
                    "nombre": producto.nombre,
                    "codigo": producto.codigo,
                    "stock_actual": stock,
                    "stock_minimo": producto.stock_minimo
                })
        
        return sorted(productos_bajo_stock, key=lambda x: x["stock_actual"])


# Instancia de CRUD para transacciones
crud_tipo_transaccion = CRUDBase[models.TipoTransaccion, schemas.TipoTransaccionCreate, schemas.TipoTransaccionCreate](models.TipoTransaccion)
crud_transaccion = CRUDTransaccion[models.Transaccion, schemas.TransaccionCreate, schemas.TransaccionCreate](models.Transaccion)

