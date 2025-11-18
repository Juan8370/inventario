import pytest
from datetime import datetime
from decimal import Decimal
from sqlalchemy.orm import Session
from app.src.database import crud, schemas
from app.src.database.models import Producto, Usuario, TipoProducto, EstadoProducto, TipoTransaccion

# ============================================================================
# FIXTURES
# ============================================================================

@pytest.fixture
def producto_test(db: Session, tipo_producto: TipoProducto, estado_producto: EstadoProducto):
    """Fixture para crear un producto de prueba"""
    producto_data = schemas.ProductoCreate(
        codigo="PROD-TEST-001",
        nombre="Producto Test Transacciones",
        descripcion="Producto para pruebas de transacciones",
        marca="TestBrand",
        modelo="TX-100",
        precio_compra=Decimal("100.00"),
        precio_venta=Decimal("150.00"),
        stock_minimo=10,
        unidad_medida="unidad",
        tipo_producto_id=tipo_producto.id,
        estado_producto_id=estado_producto.id
    )
    producto = crud.crud_producto.create(db, obj_in=producto_data)
    return producto


@pytest.fixture
def tipo_entrada(db: Session):
    """Fixture para obtener el tipo ENTRADA"""
    tipo = db.query(TipoTransaccion).filter(TipoTransaccion.nombre == "ENTRADA").first()
    if not tipo:
        tipo = TipoTransaccion(
            nombre="ENTRADA",
            descripcion="Entrada de productos"
        )
        db.add(tipo)
        db.commit()
        db.refresh(tipo)
    return tipo


@pytest.fixture
def tipo_salida(db: Session):
    """Fixture para obtener el tipo SALIDA"""
    tipo = db.query(TipoTransaccion).filter(TipoTransaccion.nombre == "SALIDA").first()
    if not tipo:
        tipo = TipoTransaccion(
            nombre="SALIDA",
            descripcion="Salida de productos"
        )
        db.add(tipo)
        db.commit()
        db.refresh(tipo)
    return tipo


# ============================================================================
# TEST TIPOS DE TRANSACCION
# ============================================================================

class TestTipoTransaccion:
    """Tests para tipos de transacción"""
    
    def test_crear_tipo_transaccion(self, db: Session):
        """Test crear tipo de transacción"""
        tipo_data = schemas.TipoTransaccionCreate(
            nombre="TEST_TIPO",
            descripcion="Tipo de prueba"
        )
        tipo = crud.crud_tipo_transaccion.create(db, obj_in=tipo_data)
        
        assert tipo.id is not None
        assert tipo.nombre == "TEST_TIPO"
        assert tipo.descripcion == "Tipo de prueba"
        assert tipo.activo is True
    
    def test_listar_tipos_transaccion(self, db: Session, tipo_entrada, tipo_salida):
        """Test listar tipos de transacción"""
        tipos = crud.crud_tipo_transaccion.get_multi(db, limit=100)
        
        assert len(tipos) >= 2
        nombres = [t.nombre for t in tipos]
        assert "ENTRADA" in nombres
        assert "SALIDA" in nombres


# ============================================================================
# TEST CRUD TRANSACCIONES
# ============================================================================

class TestTransaccionCRUD:
    """Tests para operaciones CRUD de transacciones"""
    
    def test_crear_transaccion_entrada(
        self,
        db: Session,
        usuario: Usuario,
        producto_test: Producto,
        tipo_entrada: TipoTransaccion
    ):
        """Test crear transacción de entrada"""
        transaccion_data = {
            "tipo_transaccion_id": tipo_entrada.id,
            "producto_id": producto_test.id,
            "cantidad": Decimal("50.00"),
            "usuario_id": usuario.id,
            "fecha": datetime.utcnow(),
            "observaciones": "Primera entrada de stock"
        }
        
        transaccion = crud.crud_transaccion.create(db, obj_in=transaccion_data)
        
        assert transaccion.id is not None
        assert transaccion.tipo_transaccion_id == tipo_entrada.id
        assert transaccion.producto_id == producto_test.id
        assert transaccion.cantidad == Decimal("50.00")
        assert transaccion.usuario_id == usuario.id
        assert transaccion.observaciones == "Primera entrada de stock"
    
    def test_crear_transaccion_salida(
        self,
        db: Session,
        usuario: Usuario,
        producto_test: Producto,
        tipo_salida: TipoTransaccion
    ):
        """Test crear transacción de salida"""
        transaccion_data = {
            "tipo_transaccion_id": tipo_salida.id,
            "producto_id": producto_test.id,
            "cantidad": Decimal("10.00"),
            "usuario_id": usuario.id,
            "fecha": datetime.utcnow(),
            "observaciones": "Venta de 10 unidades"
        }
        
        transaccion = crud.crud_transaccion.create(db, obj_in=transaccion_data)
        
        assert transaccion.id is not None
        assert transaccion.tipo_transaccion_id == tipo_salida.id
        assert transaccion.cantidad == Decimal("10.00")
    
    def test_obtener_transaccion_por_id(
        self,
        db: Session,
        usuario: Usuario,
        producto_test: Producto,
        tipo_entrada: TipoTransaccion
    ):
        """Test obtener transacción por ID"""
        transaccion_data = {
            "tipo_transaccion_id": tipo_entrada.id,
            "producto_id": producto_test.id,
            "cantidad": Decimal("25.00"),
            "usuario_id": usuario.id,
            "fecha": datetime.utcnow()
        }
        transaccion = crud.crud_transaccion.create(db, obj_in=transaccion_data)
        
        transaccion_obtenida = crud.crud_transaccion.get(db, transaccion.id)
        
        assert transaccion_obtenida is not None
        assert transaccion_obtenida.id == transaccion.id
        assert transaccion_obtenida.cantidad == Decimal("25.00")
    
    def test_listar_transacciones(
        self,
        db: Session,
        usuario: Usuario,
        producto_test: Producto,
        tipo_entrada: TipoTransaccion
    ):
        """Test listar transacciones con paginación"""
        # Crear varias transacciones
        for i in range(5):
            transaccion_data = {
                "tipo_transaccion_id": tipo_entrada.id,
                "producto_id": producto_test.id,
                "cantidad": Decimal(f"{i+1}.00"),
                "usuario_id": usuario.id,
                "fecha": datetime.utcnow()
            }
            crud.crud_transaccion.create(db, obj_in=transaccion_data)
        
        transacciones = crud.crud_transaccion.get_multi(db, skip=0, limit=10)
        
        assert len(transacciones) >= 5


# ============================================================================
# TEST MÉTODOS ESPECIALES
# ============================================================================

class TestMetodosEspeciales:
    """Tests para métodos especiales del CRUD de transacciones"""
    
    def test_get_by_producto(
        self,
        db: Session,
        usuario: Usuario,
        producto_test: Producto,
        tipo_entrada: TipoTransaccion,
        tipo_salida: TipoTransaccion
    ):
        """Test obtener transacciones por producto"""
        # Crear transacciones del producto
        for i in range(3):
            crud.crud_transaccion.create(db, obj_in={
                "tipo_transaccion_id": tipo_entrada.id,
                "producto_id": producto_test.id,
                "cantidad": Decimal("10.00"),
                "usuario_id": usuario.id,
                "fecha": datetime.utcnow()
            })
        
        transacciones = crud.crud_transaccion.get_by_producto(
            db,
            producto_id=producto_test.id,
            skip=0,
            limit=10
        )
        
        assert len(transacciones) >= 3
        for t in transacciones:
            assert t.producto_id == producto_test.id
    
    def test_get_entradas(
        self,
        db: Session,
        usuario: Usuario,
        producto_test: Producto,
        tipo_entrada: TipoTransaccion,
        tipo_salida: TipoTransaccion
    ):
        """Test obtener solo entradas"""
        # Crear entradas
        crud.crud_transaccion.create(db, obj_in={
            "tipo_transaccion_id": tipo_entrada.id,
            "producto_id": producto_test.id,
            "cantidad": Decimal("100.00"),
            "usuario_id": usuario.id,
            "fecha": datetime.utcnow()
        })
        
        # Crear salidas
        crud.crud_transaccion.create(db, obj_in={
            "tipo_transaccion_id": tipo_salida.id,
            "producto_id": producto_test.id,
            "cantidad": Decimal("20.00"),
            "usuario_id": usuario.id,
            "fecha": datetime.utcnow()
        })
        
        entradas = crud.crud_transaccion.get_entradas(db, producto_id=producto_test.id)
        
        assert len(entradas) >= 1
        for entrada in entradas:
            assert entrada.tipo_transaccion.nombre == "ENTRADA"
    
    def test_get_salidas(
        self,
        db: Session,
        usuario: Usuario,
        producto_test: Producto,
        tipo_entrada: TipoTransaccion,
        tipo_salida: TipoTransaccion
    ):
        """Test obtener solo salidas"""
        # Crear entrada
        crud.crud_transaccion.create(db, obj_in={
            "tipo_transaccion_id": tipo_entrada.id,
            "producto_id": producto_test.id,
            "cantidad": Decimal("100.00"),
            "usuario_id": usuario.id,
            "fecha": datetime.utcnow()
        })
        
        # Crear salidas
        for i in range(2):
            crud.crud_transaccion.create(db, obj_in={
                "tipo_transaccion_id": tipo_salida.id,
                "producto_id": producto_test.id,
                "cantidad": Decimal("15.00"),
                "usuario_id": usuario.id,
                "fecha": datetime.utcnow()
            })
        
        salidas = crud.crud_transaccion.get_salidas(db, producto_id=producto_test.id)
        
        assert len(salidas) >= 2
        for salida in salidas:
            assert salida.tipo_transaccion.nombre == "SALIDA"
    
    def test_calcular_stock_actual(
        self,
        db: Session,
        usuario: Usuario,
        producto_test: Producto,
        tipo_entrada: TipoTransaccion,
        tipo_salida: TipoTransaccion
    ):
        """Test calcular stock actual de un producto"""
        # Crear entradas
        crud.crud_transaccion.create(db, obj_in={
            "tipo_transaccion_id": tipo_entrada.id,
            "producto_id": producto_test.id,
            "cantidad": Decimal("100.00"),
            "usuario_id": usuario.id,
            "fecha": datetime.utcnow()
        })
        crud.crud_transaccion.create(db, obj_in={
            "tipo_transaccion_id": tipo_entrada.id,
            "producto_id": producto_test.id,
            "cantidad": Decimal("50.00"),
            "usuario_id": usuario.id,
            "fecha": datetime.utcnow()
        })
        
        # Crear salidas
        crud.crud_transaccion.create(db, obj_in={
            "tipo_transaccion_id": tipo_salida.id,
            "producto_id": producto_test.id,
            "cantidad": Decimal("30.00"),
            "usuario_id": usuario.id,
            "fecha": datetime.utcnow()
        })
        
        stock = crud.crud_transaccion.calcular_stock_actual(db, producto_test.id)
        
        # Stock = (100 + 50) - 30 = 120
        assert stock == 120.0
    
    def test_stock_con_solo_entradas(
        self,
        db: Session,
        usuario: Usuario,
        producto_test: Producto,
        tipo_entrada: TipoTransaccion
    ):
        """Test calcular stock solo con entradas"""
        crud.crud_transaccion.create(db, obj_in={
            "tipo_transaccion_id": tipo_entrada.id,
            "producto_id": producto_test.id,
            "cantidad": Decimal("75.00"),
            "usuario_id": usuario.id,
            "fecha": datetime.utcnow()
        })
        
        stock = crud.crud_transaccion.calcular_stock_actual(db, producto_test.id)
        assert stock == 75.0
    
    def test_stock_producto_sin_transacciones(
        self,
        db: Session,
        producto_test: Producto
    ):
        """Test calcular stock de producto sin transacciones"""
        stock = crud.crud_transaccion.calcular_stock_actual(db, producto_test.id)
        assert stock == 0.0


# ============================================================================
# TEST VALIDACIONES
# ============================================================================

class TestValidaciones:
    """Tests de validaciones en transacciones"""
    
    def test_cantidad_debe_ser_positiva(self):
        """Test que la cantidad debe ser mayor a 0"""
        with pytest.raises(Exception):  # Pydantic ValidationError
            schemas.TransaccionCreate(
                tipo_transaccion_id=1,
                producto_id=1,
                cantidad=Decimal("0.00"),  # Cantidad inválida
                fecha=datetime.utcnow()
            )
    
    def test_cantidad_no_puede_ser_negativa(self):
        """Test que la cantidad no puede ser negativa"""
        with pytest.raises(Exception):  # Pydantic ValidationError
            schemas.TransaccionCreate(
                tipo_transaccion_id=1,
                producto_id=1,
                cantidad=Decimal("-10.00"),  # Cantidad inválida
                fecha=datetime.utcnow()
            )
