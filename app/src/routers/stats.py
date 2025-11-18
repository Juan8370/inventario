from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.src.database import schemas
from app.src.database.crud import CRUDBase
from app.src.database.database import get_db
from app.src.database.models import Empresa, Producto, Usuario
from app.src.auth import get_current_user


router = APIRouter(tags=["stats"])


crud_producto = CRUDBase[Producto, schemas.ProductoCreate, schemas.ProductoUpdate](Producto)
crud_usuario = CRUDBase[Usuario, schemas.UsuarioCreate, schemas.UsuarioUpdate](Usuario)
crud_empresa = CRUDBase[Empresa, schemas.EmpresaCreate, schemas.EmpresaUpdate](Empresa)


@router.get("/stats", status_code=200)
async def obtener_estadisticas(
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user),
):
    total_productos = crud_producto.count(db)
    total_empresas = crud_empresa.count(db)
    total_usuarios = crud_usuario.count(db)

    return {
        "total_productos": total_productos,
        "total_empresas": total_empresas,
        "total_usuarios": total_usuarios,
        "database_connected": True,
        "usuario_actual": current_user.username,
    }
