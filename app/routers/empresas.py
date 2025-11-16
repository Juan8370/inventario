from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.database.database import get_db
from app.database.crud import CRUDBase
from app.database.models import Empresa, Usuario
from app.database import schemas
from app.src.auth import get_current_admin, get_current_user


router = APIRouter(prefix="/empresas", tags=["empresas"])

crud_empresa = CRUDBase[Empresa, schemas.EmpresaCreate, schemas.EmpresaUpdate](Empresa)


@router.get("", response_model=list[schemas.Empresa], status_code=200)
async def listar_empresas(
    skip: int = Query(0, ge=0),
    limit: int = Query(10, ge=1),
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user),
):
    empresas = crud_empresa.get_multi(db, skip=skip, limit=limit)
    return empresas


@router.post("", response_model=schemas.Empresa, status_code=201)
async def crear_empresa(
    empresa: schemas.EmpresaCreate,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_admin),
):
    empresa_existente = crud_empresa.get_by_field(db, "ruc", empresa.ruc)
    if empresa_existente:
        raise HTTPException(status_code=400, detail="Ya existe una empresa con este RUC")
    return crud_empresa.create(db, obj_in=empresa)
