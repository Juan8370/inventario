"""
Utilidades para crear logs del sistema
"""
from typing import Optional
from sqlalchemy.orm import Session
from app.src.database.crud import crud_log, crud_tipo_log
from app.src.database.schemas import LogCreate


class LogHelper:
    """Clase helper para facilitar la creación de logs"""
    
    # Cache de IDs de tipos de log para evitar consultas repetidas
    _tipo_log_cache = {}
    
    @classmethod
    def _get_tipo_log_id(cls, db: Session, tipo_nombre: str) -> Optional[int]:
        """Obtiene el ID del tipo de log por nombre, con caché"""
        if tipo_nombre in cls._tipo_log_cache:
            return cls._tipo_log_cache[tipo_nombre]
        
        tipo_log = crud_tipo_log.get_by_field(db, "nombre", tipo_nombre)
        if tipo_log:
            cls._tipo_log_cache[tipo_nombre] = tipo_log.id
            return tipo_log.id
        return None
    
    @classmethod
    def log_error(
        cls,
        db: Session,
        descripcion: str,
        usuario_id: Optional[int] = None,
        usuario_tipo: str = "SYSTEM"
    ):
        """
        Registrar un error crítico.
        
        Args:
            db: Sesión de base de datos
            descripcion: Descripción del error
            usuario_id: ID del usuario (opcional, requerido si usuario_tipo es USUARIO)
            usuario_tipo: SYSTEM o USUARIO
        """
        tipo_log_id = cls._get_tipo_log_id(db, "ERROR")
        if not tipo_log_id:
            return None
        
        log_data = LogCreate(
            descripcion=descripcion,
            usuario_tipo=usuario_tipo,
            tipo_log_id=tipo_log_id,
            usuario_id=usuario_id
        )
        return crud_log.create(db=db, obj_in=log_data)
    
    @classmethod
    def log_warning(
        cls,
        db: Session,
        descripcion: str,
        usuario_id: Optional[int] = None,
        usuario_tipo: str = "SYSTEM"
    ):
        """
        Registrar una advertencia no crítica.
        
        Args:
            db: Sesión de base de datos
            descripcion: Descripción de la advertencia
            usuario_id: ID del usuario (opcional, requerido si usuario_tipo es USUARIO)
            usuario_tipo: SYSTEM o USUARIO
        """
        tipo_log_id = cls._get_tipo_log_id(db, "WARNING")
        if not tipo_log_id:
            return None
        
        log_data = LogCreate(
            descripcion=descripcion,
            usuario_tipo=usuario_tipo,
            tipo_log_id=tipo_log_id,
            usuario_id=usuario_id
        )
        return crud_log.create(db=db, obj_in=log_data)
    
    @classmethod
    def log_info(
        cls,
        db: Session,
        descripcion: str,
        usuario_id: Optional[int] = None,
        usuario_tipo: str = "SYSTEM"
    ):
        """
        Registrar información sobre acciones.
        
        Args:
            db: Sesión de base de datos
            descripcion: Descripción de la acción
            usuario_id: ID del usuario (opcional, requerido si usuario_tipo es USUARIO)
            usuario_tipo: SYSTEM o USUARIO
        """
        tipo_log_id = cls._get_tipo_log_id(db, "INFO")
        if not tipo_log_id:
            return None
        
        log_data = LogCreate(
            descripcion=descripcion,
            usuario_tipo=usuario_tipo,
            tipo_log_id=tipo_log_id,
            usuario_id=usuario_id
        )
        return crud_log.create(db=db, obj_in=log_data)
    
    @classmethod
    def log_login(
        cls,
        db: Session,
        usuario_id: int,
        descripcion: str = "Usuario inició sesión"
    ):
        """
        Registrar inicio de sesión de usuario.
        
        Args:
            db: Sesión de base de datos
            usuario_id: ID del usuario
            descripcion: Descripción del login (opcional)
        """
        tipo_log_id = cls._get_tipo_log_id(db, "LOGIN")
        if not tipo_log_id:
            return None
        
        log_data = LogCreate(
            descripcion=descripcion,
            usuario_tipo="USUARIO",
            tipo_log_id=tipo_log_id,
            usuario_id=usuario_id
        )
        return crud_log.create(db=db, obj_in=log_data)
    
    @classmethod
    def log_signup(
        cls,
        db: Session,
        usuario_id: int,
        descripcion: str = "Usuario creado en el sistema"
    ):
        """
        Registrar creación de nuevo usuario.
        
        Args:
            db: Sesión de base de datos
            usuario_id: ID del usuario creado
            descripcion: Descripción del signup (opcional)
        """
        tipo_log_id = cls._get_tipo_log_id(db, "SIGNUP")
        if not tipo_log_id:
            return None
        
        log_data = LogCreate(
            descripcion=descripcion,
            usuario_tipo="USUARIO",
            tipo_log_id=tipo_log_id,
            usuario_id=usuario_id
        )
        return crud_log.create(db=db, obj_in=log_data)


# Funciones de conveniencia
def log_error(db: Session, descripcion: str, usuario_id: Optional[int] = None, usuario_tipo: str = "SYSTEM"):
    """Registrar error crítico"""
    return LogHelper.log_error(db, descripcion, usuario_id, usuario_tipo)


def log_warning(db: Session, descripcion: str, usuario_id: Optional[int] = None, usuario_tipo: str = "SYSTEM"):
    """Registrar advertencia"""
    return LogHelper.log_warning(db, descripcion, usuario_id, usuario_tipo)


def log_info(db: Session, descripcion: str, usuario_id: Optional[int] = None, usuario_tipo: str = "SYSTEM"):
    """Registrar información"""
    return LogHelper.log_info(db, descripcion, usuario_id, usuario_tipo)


def log_login(db: Session, usuario_id: int, descripcion: str = "Usuario inició sesión"):
    """Registrar login de usuario"""
    return LogHelper.log_login(db, usuario_id, descripcion)


def log_signup(db: Session, usuario_id: int, descripcion: str = "Usuario creado en el sistema"):
    """Registrar creación de usuario"""
    return LogHelper.log_signup(db, usuario_id, descripcion)
