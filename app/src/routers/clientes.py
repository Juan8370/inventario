from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.src.database.database import get_db
from app.src.database import crud, schemas, models
from app.src.auth.dependencies import get_current_user
from app.src.database.log_helper import log_info, log_error

router = APIRouter(
    prefix="/clientes",
    tags=["Clientes"],
)


@router.post("/", response_model=schemas.Cliente, status_code=201)
def crear_cliente(
    cliente: schemas.ClienteCreate,
    db: Session = Depends(get_db),
    current_user: models.Usuario = Depends(get_current_user),
):
    try:
        nuevo_cliente = crud.crud_cliente.create(db, obj_in=cliente)

        log_info(
            db=db,
            usuario_id=current_user.id,
            usuario_tipo="USUARIO",
            descripcion=f"Cliente creado: {nuevo_cliente.nombre} {nuevo_cliente.apellido} (ID: {nuevo_cliente.id})",
        )

        return nuevo_cliente
    except HTTPException:
        raise
    except Exception as e:
        log_error(
            db=db,
            usuario_id=current_user.id,
            usuario_tipo="USUARIO",
            descripcion=f"Error al crear cliente: {str(e)}",
        )
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/", response_model=List[schemas.Cliente])
def listar_clientes(
    nombre: Optional[str] = Query(None, max_length=100),
    apellido: Optional[str] = Query(None, max_length=100),
    identidad: Optional[str] = Query(None, max_length=20),
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    db: Session = Depends(get_db),
    current_user: models.Usuario = Depends(get_current_user),
):
    filters = {}
    if nombre:
        filters["nombre"] = nombre
    if apellido:
        filters["apellido"] = apellido
    if identidad:
        filters["identidad"] = identidad

    clientes = crud.crud_cliente.get_multi(db, skip=skip, limit=limit, filters=filters, order_by="nombre")
    return clientes


@router.get("/{cliente_id}", response_model=schemas.Cliente)
def obtener_cliente(
    cliente_id: int,
    db: Session = Depends(get_db),
    current_user: models.Usuario = Depends(get_current_user),
):
    cliente = crud.crud_cliente.get_or_404(db, cliente_id)
    return cliente


@router.put("/{cliente_id}", response_model=schemas.Cliente)
def actualizar_cliente(
    cliente_id: int,
    cliente_update: schemas.ClienteUpdate,
    db: Session = Depends(get_db),
    current_user: models.Usuario = Depends(get_current_user),
):
    cliente = crud.crud_cliente.get_or_404(db, cliente_id)
    try:
        cliente_actualizado = crud.crud_cliente.update(db, db_obj=cliente, obj_in=cliente_update)

        log_info(
            db=db,
            usuario_id=current_user.id,
            usuario_tipo="USUARIO",
            descripcion=f"Cliente actualizado: {cliente_actualizado.nombre} {cliente_actualizado.apellido} (ID: {cliente_id})",
        )

        return cliente_actualizado
    except Exception as e:
        log_error(
            db=db,
            usuario_id=current_user.id,
            usuario_tipo="USUARIO",
            descripcion=f"Error al actualizar cliente {cliente_id}: {str(e)}",
        )
        raise HTTPException(status_code=400, detail=str(e))