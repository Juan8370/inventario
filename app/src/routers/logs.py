"""
Router para endpoints de Logs del sistema
Los logs son INMUTABLES - solo se pueden crear y consultar
"""
from typing import Optional
from datetime import datetime
from fastapi import APIRouter, Depends, Query, HTTPException, status
from sqlalchemy.orm import Session

from app.src.database.database import get_db
from app.src.database import schemas
from app.src.database.crud import crud_log, crud_tipo_log
from app.src.database.models import Usuario
from app.src.auth.dependencies import get_current_user, get_current_admin
import math

router = APIRouter(prefix="/logs", tags=["Logs"])


@router.post("/", response_model=schemas.Log, status_code=status.HTTP_201_CREATED)
def crear_log(
    log_data: schemas.LogCreate,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user)
):
    """
    Crear un nuevo log (INMUTABLE).
    
    Solo administradores pueden crear logs manualmente.
    Los logs del sistema se crean automáticamente por la aplicación.
    """
    # Solo admins pueden crear logs manualmente
    if current_user.tipo_usuario_id != 1:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Solo administradores pueden crear logs manualmente"
        )
    
    # Verificar que el tipo de log existe
    tipo_log = crud_tipo_log.get(db, log_data.tipo_log_id)
    if not tipo_log:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Tipo de log con id {log_data.tipo_log_id} no encontrado"
        )
    
    # Si es log de usuario, verificar que el usuario existe
    if log_data.usuario_tipo == "USUARIO" and log_data.usuario_id:
        from app.src.auth.crud import crud_usuario
        usuario = crud_usuario.get(db, log_data.usuario_id)
        if not usuario:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Usuario con id {log_data.usuario_id} no encontrado"
            )
    
    return crud_log.create(db=db, obj_in=log_data)


@router.get("/", response_model=schemas.LogListResponse)
def listar_logs(
    skip: int = Query(0, ge=0, description="Número de registros a saltar"),
    limit: int = Query(50, ge=1, le=100, description="Límite de registros"),
    tipo_log_id: Optional[int] = Query(None, description="Filtrar por tipo de log"),
    usuario_id: Optional[int] = Query(None, description="Filtrar por usuario"),
    fecha_desde: Optional[datetime] = Query(None, description="Fecha desde"),
    fecha_hasta: Optional[datetime] = Query(None, description="Fecha hasta"),
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user)
):
    """
    Listar logs del sistema.
    
    - Usuarios normales solo pueden ver sus propios logs
    - Administradores pueden ver todos los logs excepto los de SYSTEM
    - Los logs de SYSTEM solo son visibles en el endpoint /logs/system (admin)
    """
    filters = {}
    
    # Usuarios normales solo ven sus propios logs
    if current_user.tipo_usuario_id != 1:
        filters["usuario_id"] = current_user.id
        filters["usuario_tipo"] = "USUARIO"
    else:
        # Admins no ven logs de SYSTEM en este endpoint
        filters["usuario_tipo"] = "USUARIO"
        
        # Aplicar filtros opcionales para admins
        if usuario_id:
            filters["usuario_id"] = usuario_id
    
    # Filtros comunes
    if tipo_log_id:
        filters["tipo_log_id"] = tipo_log_id
    
    # Filtros de fecha
    if fecha_desde or fecha_hasta:
        fecha_filters = {}
        if fecha_desde:
            fecha_filters["gte"] = fecha_desde
        if fecha_hasta:
            fecha_filters["lte"] = fecha_hasta
        if fecha_filters:
            filters["fecha"] = fecha_filters
    
    # Obtener logs
    logs = crud_log.get_multi(db, skip=skip, limit=limit, filters=filters)
    total = crud_log.count(db, filters=filters)
    
    return {
        "items": logs,
        "total": total,
        "page": (skip // limit) + 1,
        "size": limit,
        "pages": math.ceil(total / limit) if total > 0 else 0
    }


@router.get("/system", response_model=schemas.LogListResponse)
def listar_logs_sistema(
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    tipo_log_id: Optional[int] = Query(None),
    fecha_desde: Optional[datetime] = Query(None),
    fecha_hasta: Optional[datetime] = Query(None),
    db: Session = Depends(get_db),
    admin: Usuario = Depends(get_current_admin)
):
    """
    Listar logs del SYSTEM (solo administradores).
    
    Los logs de SYSTEM son invisibles para usuarios normales.
    """
    filters = {"usuario_tipo": "SYSTEM"}
    
    if tipo_log_id:
        filters["tipo_log_id"] = tipo_log_id
    
    # Filtros de fecha
    if fecha_desde or fecha_hasta:
        fecha_filters = {}
        if fecha_desde:
            fecha_filters["gte"] = fecha_desde
        if fecha_hasta:
            fecha_filters["lte"] = fecha_hasta
        if fecha_filters:
            filters["fecha"] = fecha_filters
    
    logs = crud_log.get_multi(db, skip=skip, limit=limit, filters=filters)
    total = crud_log.count(db, filters=filters)
    
    return {
        "items": logs,
        "total": total,
        "page": (skip // limit) + 1,
        "size": limit,
        "pages": math.ceil(total / limit) if total > 0 else 0
    }


@router.get("/me", response_model=schemas.LogListResponse)
def listar_mis_logs(
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    tipo_log_id: Optional[int] = Query(None),
    fecha_desde: Optional[datetime] = Query(None),
    fecha_hasta: Optional[datetime] = Query(None),
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user)
):
    """
    Listar logs del usuario actual.
    """
    filters = {
        "usuario_id": current_user.id,
        "usuario_tipo": "USUARIO"
    }
    
    if tipo_log_id:
        filters["tipo_log_id"] = tipo_log_id
    
    # Filtros de fecha
    if fecha_desde or fecha_hasta:
        fecha_filters = {}
        if fecha_desde:
            fecha_filters["gte"] = fecha_desde
        if fecha_hasta:
            fecha_filters["lte"] = fecha_hasta
        if fecha_filters:
            filters["fecha"] = fecha_filters
    
    logs = crud_log.get_multi(db, skip=skip, limit=limit, filters=filters)
    total = crud_log.count(db, filters=filters)
    
    return {
        "items": logs,
        "total": total,
        "page": (skip // limit) + 1,
        "size": limit,
        "pages": math.ceil(total / limit) if total > 0 else 0
    }


@router.get("/tipos", response_model=list[schemas.TipoLog])
def listar_tipos_log(
    db: Session = Depends(get_db),
    _: Usuario = Depends(get_current_user)
):
    """
    Listar todos los tipos de log disponibles.
    """
    return crud_tipo_log.get_multi(db, limit=100, filters={"activo": True})


@router.get("/{log_id}", response_model=schemas.Log)
def obtener_log(
    log_id: int,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user)
):
    """
    Obtener un log específico por ID.
    
    - Usuarios normales solo pueden ver sus propios logs
    - Administradores pueden ver cualquier log
    """
    log = crud_log.get(db, log_id)
    
    if not log:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Log con id {log_id} no encontrado"
        )
    
    # Usuarios normales solo pueden ver sus propios logs
    if current_user.tipo_usuario_id != 1:
        if log.usuario_tipo == "SYSTEM":
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="No tiene permisos para ver logs del sistema"
            )
        if log.usuario_id != current_user.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="No tiene permisos para ver este log"
            )
    
    return log
