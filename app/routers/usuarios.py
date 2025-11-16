from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.database.database import get_db
from app.database.crud import CRUDBase
from app.database.models import Usuario
from app.database import schemas
from app.src.auth import crud_usuario as auth_crud_usuario, get_current_admin


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

    return auth_crud_usuario.create(db, obj_in=usuario)
