from datetime import datetime
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.src.database.database import get_db
from app.src.database import crud, schemas, models
from app.src.auth.dependencies import get_current_user
from app.src.database.log_helper import log_info, log_error

router = APIRouter(
    prefix="/ventas",
    tags=["Ventas"],
)


@router.post("/", response_model=schemas.Venta, status_code=201)
def crear_venta(
    venta: schemas.VentaCreate,
    db: Session = Depends(get_db),
    current_user: models.Usuario = Depends(get_current_user),
):
    try:
        # Verificar que el cliente existe
        cliente = crud.crud_cliente.get(db, venta.cliente_id)
        if not cliente:
            raise HTTPException(status_code=404, detail="Cliente no encontrado")

        # Verificar estado de venta
        estado_venta = crud.crud_estado_venta.get(db, venta.estado_venta_id)
        if not estado_venta:
            raise HTTPException(status_code=404, detail="Estado de venta no encontrado")

        # Obtener tipo SALIDA para transacciones
        tipo_salida = crud.crud_tipo_transaccion.get_by_field(db, "nombre", "SALIDA")
        if not tipo_salida:
            raise HTTPException(status_code=400, detail="Tipo de transacción SALIDA no configurado")

        # Crear la venta
        data_venta = {
            "factura_id": venta.factura_id,
            "cliente_id": venta.cliente_id,
            "fecha": venta.fecha,
            "valor_total": venta.valor_total,
            "vendedor_id": current_user.id,
            "estado_venta_id": venta.estado_venta_id,
            "observaciones": venta.observaciones,
        }
        nueva_venta = crud.crud_venta.create(db, obj_in=data_venta)

        # Procesar detalles de venta y actualizar inventario
        for detalle in venta.detalle_ventas:
            # Verificar producto
            producto = crud.crud_producto.get(db, detalle.producto_id)
            if not producto:
                raise HTTPException(status_code=404, detail=f"Producto {detalle.producto_id} no encontrado")

            # Crear detalle de venta
            detalle_data = {
                "venta_id": nueva_venta.id,
                "producto_id": detalle.producto_id,
                "cantidad": detalle.cantidad,
                "precio_unitario": detalle.precio_unitario,
                "descuento_unitario": detalle.descuento_unitario,
                "subtotal": detalle.subtotal,
            }
            nuevo_detalle = models.DetalleVenta(**detalle_data)
            db.add(nuevo_detalle)

            # Crear transacción SALIDA
            tx_data = {
                "tipo_transaccion_id": tipo_salida.id,
                "producto_id": detalle.producto_id,
                "cantidad": float(detalle.cantidad),
                "fecha": venta.fecha,
                "observaciones": f"Venta #{nueva_venta.factura_id}",
                "compra_id": None,
                "venta_id": nueva_venta.id,
                "usuario_id": current_user.id,
            }
            transaccion = crud.crud_transaccion.create(db, obj_in=tx_data)

            # Actualizar inventario (SALIDA: restar cantidad)
            inventario = (
                db.query(models.Inventario)
                .filter(models.Inventario.producto_id == detalle.producto_id)
                .first()
            )
            if not inventario:
                raise HTTPException(
                    status_code=400,
                    detail=f"No hay inventario para el producto {detalle.producto_id}"
                )

            cantidad_int = int(detalle.cantidad)
            if inventario.cantidad_disponible < cantidad_int:
                raise HTTPException(
                    status_code=400,
                    detail=f"Stock insuficiente para el producto {producto.nombre} (disponible: {inventario.cantidad_disponible})"
                )

            inventario.cantidad_actual -= cantidad_int
            inventario.cantidad_disponible = inventario.cantidad_actual - inventario.cantidad_reservada
            inventario.fecha_ultima_salida = venta.fecha
            inventario.fecha_actualizacion = datetime.utcnow()

        db.commit()
        db.refresh(nueva_venta)

        log_info(
            db=db,
            usuario_id=current_user.id,
            usuario_tipo="USUARIO",
            descripcion=f"Venta creada con ID {nueva_venta.id} (factura={nueva_venta.factura_id}, cliente={cliente.nombre} {cliente.apellido})",
        )

        return nueva_venta
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        log_error(
            db=db,
            usuario_id=current_user.id,
            usuario_tipo="USUARIO",
            descripcion=f"Error al crear venta: {str(e)}",
        )
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/", response_model=List[schemas.Venta])
def listar_ventas(
    cliente_id: Optional[int] = Query(None, gt=0),
    fecha_desde: Optional[datetime] = Query(None),
    fecha_hasta: Optional[datetime] = Query(None),
    factura_id: Optional[str] = Query(None, max_length=50),
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    db: Session = Depends(get_db),
    current_user: models.Usuario = Depends(get_current_user),
):
    filters = {}
    if cliente_id:
        filters["cliente_id"] = cliente_id
    if fecha_desde or fecha_hasta:
        rango = {}
        if fecha_desde:
            rango["gte"] = fecha_desde
        if fecha_hasta:
            rango["lte"] = fecha_hasta
        filters["fecha"] = rango
    if factura_id:
        filters["factura_id"] = factura_id

    ventas = crud.crud_venta.get_multi(db, skip=skip, limit=limit, filters=filters, order_by="fecha")
    return ventas


@router.get("/{venta_id}", response_model=schemas.Venta)
def obtener_venta(
    venta_id: int,
    db: Session = Depends(get_db),
    current_user: models.Usuario = Depends(get_current_user),
):
    venta = crud.crud_venta.get_or_404(db, venta_id)
    return venta


@router.get("/{venta_id}/detalles", response_model=List[schemas.DetalleVenta])
def listar_detalles_venta(
    venta_id: int,
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=200),
    db: Session = Depends(get_db),
    current_user: models.Usuario = Depends(get_current_user),
):
    # Verificar venta existente
    venta = crud.crud_venta.get(db, venta_id)
    if not venta:
        raise HTTPException(status_code=404, detail="Venta no encontrada")

    detalles = (
        db.query(models.DetalleVenta)
        .filter(models.DetalleVenta.venta_id == venta_id)
        .offset(skip)
        .limit(limit)
        .all()
    )
    return detalles