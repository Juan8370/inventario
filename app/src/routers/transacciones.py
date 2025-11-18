from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List
from app.src.database.database import get_db
from app.src.database import crud, schemas, models
from app.src.auth.dependencies import get_current_user, get_current_admin
from app.src.database.log_helper import log_info, log_error

router = APIRouter(
    prefix="/transacciones",
    tags=["Transacciones"]
)

@router.post("/", response_model=schemas.Transaccion, status_code=201)
def crear_transaccion(
    transaccion: schemas.TransaccionCreate,
    db: Session = Depends(get_db),
    current_user: models.Usuario = Depends(get_current_user)
):
    """
    Crea una nueva transacción de inventario (ENTRADA o SALIDA)
    
    **Requiere autenticación**
    
    - **tipo_transaccion_id**: 1=ENTRADA, 2=SALIDA
    - **producto_id**: ID del producto
    - **cantidad**: Cantidad (siempre positiva)
    - **fecha**: Fecha de la transacción
    - **observaciones**: Motivo o notas (opcional)
    
    **IMPORTANTE**: Actualiza automáticamente el inventario del producto
    """
    try:
        # Verificar que el producto existe
        producto = crud.crud_producto.get(db, transaccion.producto_id)
        if not producto:
            raise HTTPException(status_code=404, detail="Producto no encontrado")
        
        # Verificar que el tipo de transacción existe
        tipo = crud.crud_tipo_transaccion.get(db, transaccion.tipo_transaccion_id)
        if not tipo:
            raise HTTPException(status_code=404, detail="Tipo de transacción no encontrado")
        
        # Validar stock suficiente para salidas
        if tipo.nombre == "SALIDA":
            stock_actual = crud.crud_transaccion.calcular_stock_actual(db, transaccion.producto_id)
            if stock_actual < float(transaccion.cantidad):
                raise HTTPException(
                    status_code=400, 
                    detail=f"Stock insuficiente. Stock actual: {stock_actual}, Cantidad solicitada: {transaccion.cantidad}"
                )
        
        # Crear transacción con el usuario actual
        transaccion_data = transaccion.model_dump()
        transaccion_data["usuario_id"] = current_user.id
        
        nueva_transaccion = crud.crud_transaccion.create(db, obj_in=transaccion_data)
        
        # Actualizar inventario
        from datetime import datetime
        inventario = db.query(models.Inventario).filter(
            models.Inventario.producto_id == transaccion.producto_id
        ).first()
        
        if not inventario:
            # Crear registro de inventario si no existe
            inventario = models.Inventario(
                producto_id=transaccion.producto_id,
                cantidad_actual=0,
                cantidad_reservada=0,
                cantidad_disponible=0
            )
            db.add(inventario)
            db.flush()
        
        # Actualizar cantidades según el tipo de transacción
        if tipo.nombre == "ENTRADA":
            inventario.cantidad_actual += int(transaccion.cantidad)
            inventario.cantidad_disponible = inventario.cantidad_actual - inventario.cantidad_reservada
            inventario.fecha_ultima_entrada = datetime.utcnow()
        elif tipo.nombre == "SALIDA":
            inventario.cantidad_actual -= int(transaccion.cantidad)
            inventario.cantidad_disponible = inventario.cantidad_actual - inventario.cantidad_reservada
            inventario.fecha_ultima_salida = datetime.utcnow()
        
        inventario.fecha_actualizacion = datetime.utcnow()
        db.commit()
        db.refresh(nueva_transaccion)
        
        # Registrar log
        log_info(
            db=db,
            usuario_id=current_user.id,
            usuario_tipo="USUARIO",
            descripcion=f"Transacción {tipo.nombre} registrada: {producto.nombre} (cantidad: {transaccion.cantidad}). Inventario actualizado: {inventario.cantidad_actual}"
        )
        
        return nueva_transaccion
    
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        log_error(
            db=db,
            usuario_id=current_user.id,
            usuario_tipo="USUARIO",
            descripcion=f"Error al crear transacción: {str(e)}"
        )
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/", response_model=List[schemas.Transaccion])
def listar_transacciones(
    skip: int = Query(0, ge=0, description="Registros a saltar"),
    limit: int = Query(50, ge=1, le=100, description="Cantidad de registros a retornar"),
    db: Session = Depends(get_db),
    current_user: models.Usuario = Depends(get_current_user)
):
    """
    Lista todas las transacciones con paginación
    
    **Requiere autenticación**
    """
    transacciones = crud.crud_transaccion.get_multi(db, skip=skip, limit=limit)
    return transacciones


@router.get("/{transaccion_id}", response_model=schemas.Transaccion)
def obtener_transaccion(
    transaccion_id: int,
    db: Session = Depends(get_db),
    current_user: models.Usuario = Depends(get_current_user)
):
    """
    Obtiene una transacción específica por ID
    
    **Requiere autenticación**
    """
    transaccion = crud.crud_transaccion.get(db, transaccion_id)
    if not transaccion:
        raise HTTPException(status_code=404, detail="Transacción no encontrada")
    return transaccion


@router.get("/producto/{producto_id}", response_model=List[schemas.Transaccion])
def listar_transacciones_producto(
    producto_id: int,
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    db: Session = Depends(get_db),
    current_user: models.Usuario = Depends(get_current_user)
):
    """
    Lista todas las transacciones de un producto específico
    
    **Requiere autenticación**
    
    Útil para ver el historial completo de movimientos de un producto
    """
    # Verificar que el producto existe
    producto = crud.crud_producto.get(db, producto_id)
    if not producto:
        raise HTTPException(status_code=404, detail="Producto no encontrado")
    
    transacciones = crud.crud_transaccion.get_by_producto(
        db,
        producto_id=producto_id,
        skip=skip,
        limit=limit
    )
    return transacciones


@router.get("/stock/{producto_id}")
def obtener_stock_producto(
    producto_id: int,
    db: Session = Depends(get_db),
    current_user: models.Usuario = Depends(get_current_user)
):
    """
    Calcula el stock actual de un producto basado en sus transacciones
    
    **Requiere autenticación**
    
    Fórmula: SUMA(ENTRADAS) - SUMA(SALIDAS)
    """
    # Verificar que el producto existe
    producto = crud.crud_producto.get(db, producto_id)
    if not producto:
        raise HTTPException(status_code=404, detail="Producto no encontrado")
    
    stock_actual = crud.crud_transaccion.calcular_stock_actual(db, producto_id)
    
    return {
        "producto_id": producto_id,
        "codigo": producto.codigo,
        "nombre": producto.nombre,
        "stock_actual": stock_actual,
        "stock_minimo": producto.stock_minimo,
        "bajo_stock": stock_actual < producto.stock_minimo
    }


@router.get("/entradas/")
def listar_entradas(
    producto_id: int = Query(None, description="Filtrar por producto (opcional)"),
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    db: Session = Depends(get_db),
    current_user: models.Usuario = Depends(get_current_user)
):
    """
    Lista solo las transacciones de tipo ENTRADA
    
    **Requiere autenticación**
    """
    entradas = crud.crud_transaccion.get_entradas(
        db,
        producto_id=producto_id,
        skip=skip,
        limit=limit
    )
    return entradas


@router.get("/salidas/")
def listar_salidas(
    producto_id: int = Query(None, description="Filtrar por producto (opcional)"),
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    db: Session = Depends(get_db),
    current_user: models.Usuario = Depends(get_current_user)
):
    """
    Lista solo las transacciones de tipo SALIDA
    
    **Requiere autenticación**
    """
    salidas = crud.crud_transaccion.get_salidas(
        db,
        producto_id=producto_id,
        skip=skip,
        limit=limit
    )
    return salidas


@router.get("/reportes/bajo-stock")
def productos_bajo_stock(
    limite: int = Query(10, ge=0, description="Stock mínimo considerado 'bajo'"),
    db: Session = Depends(get_db),
    current_user: models.Usuario = Depends(get_current_user)
):
    """
    Obtiene productos con stock por debajo del límite especificado
    
    **Requiere autenticación**
    
    Útil para reportes de reabastecimiento
    """
    productos = crud.crud_transaccion.get_productos_bajo_stock(db, limite_stock=limite)
    
    return {
        "limite_stock": limite,
        "total_productos": len(productos),
        "productos": productos
    }


@router.get("/tipos/", response_model=List[schemas.TipoTransaccion])
def listar_tipos_transaccion(
    db: Session = Depends(get_db),
    current_user: models.Usuario = Depends(get_current_user)
):
    """
    Lista todos los tipos de transacción disponibles
    
    **Requiere autenticación**
    """
    tipos = crud.crud_tipo_transaccion.get_multi(db, limit=100)
    return tipos
