from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.src.database.database import get_db
from app.src.database.crud import CRUDBase
from app.src.database.models import Usuario
from app.src.database import schemas
from app.src.auth import crud_usuario as auth_crud_usuario, get_current_admin
from app.src.database.log_helper import log_signup, log_info


router = APIRouter(prefix="/usuarios", tags=["usuarios"])

crud_usuario = CRUDBase[Usuario, schemas.UsuarioCreate, schemas.UsuarioUpdate](Usuario)


@router.get("", response_model=list[schemas.Usuario], status_code=200)
async def listar_usuarios(
    skip: int = Query(0, ge=0),
    limit: int = Query(10, ge=1),
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_admin),
):
    usuarios = crud_usuario.get_multi(db, skip=skip, limit=limit)
    return usuarios


@router.post("", response_model=schemas.Usuario, status_code=201)
async def crear_usuario(
    usuario: schemas.UsuarioCreate,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_admin),
):
    if auth_crud_usuario.get_by_email(db, usuario.email):
        raise HTTPException(status_code=400, detail="Ya existe un usuario con este email")

    if auth_crud_usuario.get_by_username(db, usuario.username):
        raise HTTPException(status_code=400, detail="Ya existe un usuario con este username")

    nuevo_usuario = auth_crud_usuario.create(db, obj_in=usuario)
    
    # Registrar signup
    try:
        log_signup(
            db,
            usuario_id=nuevo_usuario.id,
            descripcion=f"Nuevo usuario registrado: {nuevo_usuario.username} ({nuevo_usuario.email})"
        )
        # Log adicional del admin que lo creó
        log_info(
            db,
            f"Admin creó nuevo usuario: {nuevo_usuario.username}",
            usuario_id=current_user.id,
            usuario_tipo="USUARIO"
        )
    except Exception:
        pass
    
    return nuevo_usuario
