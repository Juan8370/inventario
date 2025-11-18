from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.src.database.database import get_db
from app.src.database.crud import CRUDBase
from app.src.database.models import Producto, Usuario
from app.src.database import schemas
from app.src.auth import get_current_user, get_optional_user, get_current_admin
from app.src.database.log_helper import log_info, log_error


router = APIRouter(prefix="/productos", tags=["productos"])

crud_producto = CRUDBase[Producto, schemas.ProductoCreate, schemas.ProductoUpdate](Producto)


@router.get("", response_model=list[schemas.Producto], status_code=200)
async def listar_productos(
    skip: int = Query(0, ge=0),
    limit: int = Query(10, ge=1),
    db: Session = Depends(get_db),
    current_user: Usuario | None = Depends(get_optional_user),
):
    productos = crud_producto.get_multi(db, skip=skip, limit=limit)
    return productos


@router.get("/{producto_id}", response_model=schemas.Producto, status_code=200)
async def obtener_producto(
    producto_id: int,
    db: Session = Depends(get_db),
    current_user: Usuario | None = Depends(get_optional_user),
):
    return crud_producto.get_or_404(db, producto_id)


@router.post("", response_model=schemas.Producto, status_code=201)
async def crear_producto(
    producto: schemas.ProductoCreate,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user),
):
    producto_existente = crud_producto.get_by_field(db, "codigo", producto.codigo)
    if producto_existente:
        raise HTTPException(status_code=400, detail="Ya existe un producto con este código")
    
    nuevo_producto = crud_producto.create(db, obj_in=producto)
    
    # Registrar creación de producto
    try:
        log_info(
            db,
            f"Producto creado: {nuevo_producto.nombre} (código: {nuevo_producto.codigo})",
            usuario_id=current_user.id,
            usuario_tipo="USUARIO"
        )
    except Exception:
        pass  # No fallar la creación por error en logging
    
    return nuevo_producto


@router.put("/{producto_id}", response_model=schemas.Producto, status_code=200)
async def actualizar_producto(
    producto_id: int,
    producto: schemas.ProductoUpdate,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user),
):
    db_producto = crud_producto.get_or_404(db, producto_id)
    producto_actualizado = crud_producto.update(db, db_obj=db_producto, obj_in=producto)
    
    # Registrar actualización
    try:
        log_info(
            db,
            f"Producto actualizado: {producto_actualizado.nombre} (ID: {producto_id})",
            usuario_id=current_user.id,
            usuario_tipo="USUARIO"
        )
    except Exception:
        pass
    
    return producto_actualizado


@router.delete("/{producto_id}", status_code=200)
async def eliminar_producto(
    producto_id: int,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_admin),
):
    producto = crud_producto.delete(db, id=producto_id)
    
    # Registrar eliminación
    try:
        log_info(
            db,
            f"Producto eliminado: {producto.nombre} (código: {producto.codigo})",
            usuario_id=current_user.id,
            usuario_tipo="USUARIO"
        )
    except Exception:
        pass
    
    return {"message": f"Producto {producto.nombre} eliminado correctamente"}


@router.get("/buscar/{termino}", status_code=200)
async def buscar_productos(
    termino: str,
    skip: int = Query(0, ge=0),
    limit: int = Query(10, ge=1),
    db: Session = Depends(get_db),
    current_user: Usuario | None = Depends(get_optional_user),
):
    productos = crud_producto.search(
        db,
        search_fields=["nombre", "codigo", "descripcion", "marca"],
        search_term=termino,
        skip=skip,
        limit=limit,
    )
    return productos
