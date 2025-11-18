from datetime import datetime
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.src.database.database import get_db
from app.src.database import crud, schemas, models
from app.src.auth.dependencies import get_current_user
from app.src.database.log_helper import log_info, log_error

router = APIRouter(
    prefix="/compras",
    tags=["Compras"],
)


@router.post("/", response_model=schemas.Compra, status_code=201)
def crear_compra(
    compra: schemas.CompraCreate,
    db: Session = Depends(get_db),
    current_user: models.Usuario = Depends(get_current_user),
):
    try:
        data = compra.model_dump()
        data["usuario_id"] = current_user.id
        nueva_compra = crud.crud_compra.create(db, obj_in=data)

        log_info(
            db=db,
            usuario_id=current_user.id,
            usuario_tipo="USUARIO",
            descripcion=f"Compra creada con ID {nueva_compra.id} (proveedor_id={nueva_compra.proveedor_id}, numero={nueva_compra.numero_compra})",
        )

        return nueva_compra
    except HTTPException:
        raise
    except Exception as e:
        log_error(
            db=db,
            usuario_id=current_user.id,
            usuario_tipo="USUARIO",
            descripcion=f"Error al crear compra: {str(e)}",
        )
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/", response_model=List[schemas.Compra])
def listar_compras(
    proveedor_id: Optional[int] = Query(None, gt=0),
    fecha_desde: Optional[datetime] = Query(None),
    fecha_hasta: Optional[datetime] = Query(None),
    numero: Optional[str] = Query(None, max_length=50),
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    db: Session = Depends(get_db),
    current_user: models.Usuario = Depends(get_current_user),
):
    filters = {}
    if proveedor_id:
        filters["proveedor_id"] = proveedor_id
    if fecha_desde or fecha_hasta:
        rango = {}
        if fecha_desde:
            rango["gte"] = fecha_desde
        if fecha_hasta:
            rango["lte"] = fecha_hasta
        filters["fecha_compra"] = rango
    if numero:
        # Búsqueda simple por igualdad usando get_multi; para LIKE usar search()
        filters["numero_compra"] = numero

    compras = crud.crud_compra.get_multi(db, skip=skip, limit=limit, filters=filters, order_by="fecha_compra")
    return compras


@router.get("/{compra_id}", response_model=schemas.Compra)
def obtener_compra(
    compra_id: int,
    db: Session = Depends(get_db),
    current_user: models.Usuario = Depends(get_current_user),
):
    compra = crud.crud_compra.get_or_404(db, compra_id)
    return compra


@router.post("/{compra_id}/transacciones", response_model=List[schemas.Transaccion], status_code=201)
def agregar_items_compra(
    compra_id: int,
    payload: schemas.CompraAgregarItemsRequest,
    db: Session = Depends(get_db),
    current_user: models.Usuario = Depends(get_current_user),
):
    # Verificar compra existente
    compra = crud.crud_compra.get(db, compra_id)
    if not compra:
        raise HTTPException(status_code=404, detail="Compra no encontrada")

    # Obtener tipo ENTRADA
    tipo_entrada = crud.crud_tipo_transaccion.get_by_field(db, "nombre", "ENTRADA")
    if not tipo_entrada:
        raise HTTPException(status_code=400, detail="Tipo de transacción ENTRADA no configurado")

    creadas: List[models.Transaccion] = []
    try:
        for item in payload.items:
            # Validar producto
            producto = crud.crud_producto.get(db, item.producto_id)
            if not producto:
                raise HTTPException(status_code=404, detail=f"Producto {item.producto_id} no encontrado")

            # Crear transacción ENTRADA asociada a la compra
            tx_data = {
                "tipo_transaccion_id": tipo_entrada.id,
                "producto_id": item.producto_id,
                "cantidad": float(item.cantidad),
                "fecha": datetime.utcnow(),
                "observaciones": item.observaciones or f"Compra #{compra_id}",
                "compra_id": compra_id,
                "usuario_id": current_user.id,
                "venta_id": None,
            }
            transaccion = crud.crud_transaccion.create(db, obj_in=tx_data)

            # Actualizar inventario (lógica similar al router de transacciones)
            inventario = (
                db.query(models.Inventario)
                .filter(models.Inventario.producto_id == item.producto_id)
                .first()
            )
            if not inventario:
                inventario = models.Inventario(
                    producto_id=item.producto_id,
                    cantidad_actual=0,
                    cantidad_reservada=0,
                    cantidad_disponible=0,
                )
                db.add(inventario)
                db.flush()

            # ENTRADA: sumar cantidad
            cantidad_int = int(item.cantidad)
            inventario.cantidad_actual += cantidad_int
            inventario.cantidad_disponible = inventario.cantidad_actual - inventario.cantidad_reservada
            inventario.fecha_ultima_entrada = datetime.utcnow()
            inventario.fecha_actualizacion = datetime.utcnow()

            db.commit()
            db.refresh(transaccion)
            creadas.append(transaccion)

        log_info(
            db=db,
            usuario_id=current_user.id,
            usuario_tipo="USUARIO",
            descripcion=f"Se agregaron {len(creadas)} items a la compra {compra_id}",
        )
        return creadas
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        log_error(
            db=db,
            usuario_id=current_user.id,
            usuario_tipo="USUARIO",
            descripcion=f"Error al agregar items a compra {compra_id}: {str(e)}",
        )
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/{compra_id}/transacciones", response_model=List[schemas.Transaccion])
def listar_items_compra(
    compra_id: int,
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=200),
    db: Session = Depends(get_db),
    current_user: models.Usuario = Depends(get_current_user),
):
    # Verificar compra existente
    compra = crud.crud_compra.get(db, compra_id)
    if not compra:
        raise HTTPException(status_code=404, detail="Compra no encontrada")

    transacciones = crud.crud_transaccion.get_multi(
        db,
        skip=skip,
        limit=limit,
        filters={"compra_id": compra_id},
        order_by="fecha",
    )
    return transacciones
