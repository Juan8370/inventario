from typing import Generic, TypeVar, Type, Optional, List, Any, Dict
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_
from fastapi import HTTPException
from pydantic import BaseModel
from app.database.models import Base

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

    def create(self, db: Session, *, obj_in: CreateSchemaType) -> ModelType:
        """
        Crea un nuevo registro.
        
        Args:
            db: Sesión de base de datos
            obj_in: Esquema Pydantic con los datos
            
        Returns:
            Registro creado
        """
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
