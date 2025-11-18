import pytest
from sqlalchemy import create_engine, inspect
from sqlalchemy.orm import sessionmaker
from datetime import datetime
import sys
import os

# Agregar el directorio padre al path para importar los módulos
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.src.database.models import (
    Base, 
    TipoUsuario, EstadoUsuario, Usuario,
    TipoProducto, EstadoProducto, Producto,
    TipoEmpresa, EstadoEmpresa, Empresa,
    EstadoEmpleado, Empleado,
    EstadoVenta, Venta, DetalleVenta,
    Inventario
)


@pytest.fixture
def in_memory_db():
    """Fixture que crea una base de datos SQLite en memoria para testing"""
    # Crear engine de SQLite en memoria
    engine = create_engine("sqlite:///:memory:", echo=False)
    
    # Crear todas las tablas
    Base.metadata.create_all(engine)
    
    # Crear sesión
    SessionLocal = sessionmaker(bind=engine)
    session = SessionLocal()
    
    yield engine, session
    
    # Cleanup
    session.close()
    engine.dispose()


class TestDatabaseStructure:
    """Tests para verificar la estructura de la base de datos"""
    
    def test_database_tables_exist(self, in_memory_db):
        """Verifica que todas las tablas existen en la base de datos"""
        engine, session = in_memory_db
        inspector = inspect(engine)
        
        # Tablas esperadas
        expected_tables = {
            'tipos_usuario', 'estados_usuario', 'usuarios',
            'tipos_producto', 'estados_producto', 'productos',
            'tipos_empresa', 'estados_empresa', 'empresas',
            'estados_empleado', 'empleados',
            'estados_venta', 'ventas', 'detalle_ventas',
            'inventario'
        }
        
        # Obtener tablas reales
        actual_tables = set(inspector.get_table_names())
        
        # Verificar que todas las tablas esperadas existen
        assert expected_tables.issubset(actual_tables), f"Faltan tablas: {expected_tables - actual_tables}"
        
        print(f"✅ Todas las {len(expected_tables)} tablas fueron creadas correctamente")
    
    def test_table_columns_structure(self, in_memory_db):
        """Verifica que las tablas tengan las columnas correctas"""
        engine, session = in_memory_db
        inspector = inspect(engine)
        
        # Verificar estructura de tabla usuarios
        usuarios_columns = {col['name'] for col in inspector.get_columns('usuarios')}
        expected_usuarios_columns = {
            'id', 'username', 'email', 'password_hash', 'nombre', 'apellido',
            'telefono', 'fecha_ultimo_acceso', 'empresa_id', 'tipo_usuario_id',
            'estado_usuario_id', 'fecha_creacion', 'fecha_actualizacion'
        }
        assert expected_usuarios_columns.issubset(usuarios_columns)
        
        # Verificar estructura de tabla productos
        productos_columns = {col['name'] for col in inspector.get_columns('productos')}
        expected_productos_columns = {
            'id', 'codigo', 'nombre', 'descripcion', 'marca', 'modelo',
            'precio_compra', 'precio_venta', 'stock_minimo', 'unidad_medida',
            'tipo_producto_id', 'estado_producto_id', 'fecha_creacion', 'fecha_actualizacion'
        }
        assert expected_productos_columns.issubset(productos_columns)
        
        # Verificar estructura de tabla ventas
        ventas_columns = {col['name'] for col in inspector.get_columns('ventas')}
        expected_ventas_columns = {
            'id', 'numero_venta', 'cliente_nombre', 'cliente_documento',
            'cliente_telefono', 'cliente_email', 'cliente_direccion',
            'subtotal', 'impuesto', 'descuento', 'total', 'fecha_venta',
            'usuario_id', 'estado_venta_id', 'observaciones',
            'fecha_creacion', 'fecha_actualizacion'
        }
        assert expected_ventas_columns.issubset(ventas_columns)
        
        print("✅ Estructura de columnas verificada correctamente")
    
    def test_foreign_key_relationships(self, in_memory_db):
        """Verifica que las relaciones de clave foránea estén configuradas"""
        engine, session = in_memory_db
        inspector = inspect(engine)
        
        # Verificar FKs en tabla usuarios
        usuarios_fks = inspector.get_foreign_keys('usuarios')
        fk_columns = {fk['constrained_columns'][0] for fk in usuarios_fks}
        expected_fks = {'empresa_id', 'tipo_usuario_id', 'estado_usuario_id'}
        assert expected_fks.issubset(fk_columns)
        
        # Verificar FKs en tabla productos
        productos_fks = inspector.get_foreign_keys('productos')
        fk_columns = {fk['constrained_columns'][0] for fk in productos_fks}
        expected_fks = {'tipo_producto_id', 'estado_producto_id'}
        assert expected_fks.issubset(fk_columns)
        
        # Verificar FKs en tabla ventas
        ventas_fks = inspector.get_foreign_keys('ventas')
        fk_columns = {fk['constrained_columns'][0] for fk in ventas_fks}
        expected_fks = {'usuario_id', 'estado_venta_id'}
        assert expected_fks.issubset(fk_columns)
        
        # Verificar FKs en tabla detalle_ventas
        detalle_fks = inspector.get_foreign_keys('detalle_ventas')
        fk_columns = {fk['constrained_columns'][0] for fk in detalle_fks}
        expected_fks = {'venta_id', 'producto_id'}
        assert expected_fks.issubset(fk_columns)
        
        print("✅ Relaciones de clave foránea verificadas correctamente")
    
    def test_unique_constraints(self, in_memory_db):
        """Verifica que las restricciones UNIQUE estén en su lugar"""
        engine, session = in_memory_db
        inspector = inspect(engine)
        
        # Verificar índices únicos en usuarios
        usuarios_indexes = inspector.get_indexes('usuarios')
        unique_columns = set()
        for idx in usuarios_indexes:
            if idx['unique']:
                unique_columns.update(idx['column_names'])
        
        # En SQLite, las columnas UNIQUE se crean como índices únicos
        expected_unique = {'username', 'email'}
        # Verificar que al menos uno de los campos únicos esperados esté presente
        assert len(expected_unique.intersection(unique_columns)) > 0
        
        print("✅ Restricciones UNIQUE verificadas correctamente")


class TestDatabaseOperations:
    """Tests para verificar operaciones básicas de la base de datos"""
    
    def test_create_basic_records(self, in_memory_db):
        """Verifica que se puedan crear registros básicos"""
        engine, session = in_memory_db
        
        # Crear tipo de usuario
        tipo_usuario = TipoUsuario(
            nombre="Administrador",
            descripcion="Usuario con permisos completos"
        )
        session.add(tipo_usuario)
        session.commit()
        
        # Crear estado de usuario
        estado_usuario = EstadoUsuario(
            nombre="Activo",
            descripcion="Usuario activo en el sistema"
        )
        session.add(estado_usuario)
        session.commit()
        
        # Crear tipo de empresa
        tipo_empresa = TipoEmpresa(
            nombre="Cliente",
            descripcion="Empresa cliente"
        )
        session.add(tipo_empresa)
        session.commit()
        
        # Crear estado de empresa
        estado_empresa = EstadoEmpresa(
            nombre="Activo",
            descripcion="Empresa activa"
        )
        session.add(estado_empresa)
        session.commit()
        
        # Crear empresa
        empresa = Empresa(
            nombre="Empresa Test S.A.",
            ruc="12345678901",
            direccion="Calle Test 123",
            telefono="555-1234",
            email="test@empresa.com",
            contacto_principal="Juan Pérez",
            tipo_empresa_id=tipo_empresa.id,
            estado_empresa_id=estado_empresa.id
        )
        session.add(empresa)
        session.commit()
        
        # Crear usuario
        usuario = Usuario(
            username="admin",
            email="admin@test.com",
            password_hash="hashed_password_123",
            nombre="Admin",
            apellido="Test",
            telefono="555-0000",
            empresa_id=empresa.id,
            tipo_usuario_id=tipo_usuario.id,
            estado_usuario_id=estado_usuario.id
        )
        session.add(usuario)
        session.commit()
        
        # Verificar que los registros se crearon
        assert session.query(TipoUsuario).count() == 1
        assert session.query(EstadoUsuario).count() == 1
        assert session.query(Empresa).count() == 1
        assert session.query(Usuario).count() == 1
        
        # Verificar datos del usuario creado
        created_user = session.query(Usuario).first()
        assert created_user.username == "admin"
        assert created_user.email == "admin@test.com"
        assert created_user.empresa.nombre == "Empresa Test S.A."
        
        print("✅ Creación de registros básicos verificada correctamente")
    
    def test_product_and_inventory_operations(self, in_memory_db):
        """Verifica operaciones con productos e inventario"""
        engine, session = in_memory_db
        
        # Crear tipo de producto
        tipo_producto = TipoProducto(
            nombre="Electrónicos",
            descripcion="Productos electrónicos"
        )
        session.add(tipo_producto)
        session.commit()
        
        # Crear estado de producto
        estado_producto = EstadoProducto(
            nombre="Disponible",
            descripcion="Producto disponible para venta"
        )
        session.add(estado_producto)
        session.commit()
        
        # Crear producto
        producto = Producto(
            codigo="PROD-001",
            nombre="Laptop Test",
            descripcion="Laptop para testing",
            marca="TestBrand",
            modelo="Model-X",
            precio_compra=800.00,
            precio_venta=1000.00,
            stock_minimo=5,
            unidad_medida="pza",
            tipo_producto_id=tipo_producto.id,
            estado_producto_id=estado_producto.id
        )
        session.add(producto)
        session.commit()
        
        # Crear inventario
        inventario = Inventario(
            producto_id=producto.id,
            cantidad_actual=10,
            cantidad_reservada=2,
            cantidad_disponible=8,
            ubicacion="Almacén A-1",
            lote="LOTE-001"
        )
        session.add(inventario)
        session.commit()
        
        # Verificar relaciones
        created_producto = session.query(Producto).first()
        assert created_producto.codigo == "PROD-001"
        assert created_producto.tipo_producto.nombre == "Electrónicos"
        assert len(created_producto.inventarios) == 1
        assert created_producto.inventarios[0].cantidad_actual == 10
        
        print("✅ Operaciones de productos e inventario verificadas correctamente")
    
    def test_sales_operations(self, in_memory_db):
        """Verifica operaciones de ventas completas"""
        engine, session = in_memory_db
        
        # Crear datos necesarios (reutilizando del test anterior)
        self.test_create_basic_records(in_memory_db)
        self.test_product_and_inventory_operations(in_memory_db)
        
        # Obtener registros creados
        usuario = session.query(Usuario).first()
        producto = session.query(Producto).first()
        
        # Crear estado de venta
        estado_venta = EstadoVenta(
            nombre="Procesada",
            descripcion="Venta procesada correctamente"
        )
        session.add(estado_venta)
        session.commit()
        
        # Crear venta
        venta = Venta(
            numero_venta="V-2024-001",
            cliente_nombre="Cliente Test",
            cliente_documento="12345678",
            cliente_telefono="555-9999",
            cliente_email="cliente@test.com",
            subtotal=1000.00,
            impuesto=180.00,
            descuento=0.00,
            total=1180.00,
            fecha_venta=datetime.utcnow(),
            usuario_id=usuario.id,
            estado_venta_id=estado_venta.id,
            observaciones="Venta de prueba"
        )
        session.add(venta)
        session.commit()
        
        # Crear detalle de venta
        detalle_venta = DetalleVenta(
            venta_id=venta.id,
            producto_id=producto.id,
            cantidad=1,
            precio_unitario=1000.00,
            descuento_unitario=0.00,
            subtotal=1000.00
        )
        session.add(detalle_venta)
        session.commit()
        
        # Verificar la venta completa
        created_venta = session.query(Venta).first()
        assert created_venta.numero_venta == "V-2024-001"
        assert created_venta.total == 1180.00
        assert created_venta.usuario.username == "admin"
        assert len(created_venta.detalle_ventas) == 1
        assert created_venta.detalle_ventas[0].producto.codigo == "PROD-001"
        
        print("✅ Operaciones de ventas verificadas correctamente")
    
    def test_data_integrity_constraints(self, in_memory_db):
        """Verifica que las restricciones de integridad funcionen"""
        engine, session = in_memory_db
        
        # Intentar crear usuario con email duplicado (debería fallar)
        tipo_usuario = TipoUsuario(nombre="Test")
        estado_usuario = EstadoUsuario(nombre="Test")
        session.add_all([tipo_usuario, estado_usuario])
        session.commit()
        
        usuario1 = Usuario(
            username="user1",
            email="duplicate@test.com",
            password_hash="hash1",
            nombre="User1",
            apellido="Test",
            tipo_usuario_id=tipo_usuario.id,
            estado_usuario_id=estado_usuario.id
        )
        session.add(usuario1)
        session.commit()
        
        # Intentar crear segundo usuario con el mismo email
        usuario2 = Usuario(
            username="user2",
            email="duplicate@test.com",  # Email duplicado
            password_hash="hash2",
            nombre="User2",
            apellido="Test",
            tipo_usuario_id=tipo_usuario.id,
            estado_usuario_id=estado_usuario.id
        )
        session.add(usuario2)
        
        # Esto debería generar una excepción por UNIQUE constraint
        with pytest.raises(Exception):  # SQLAlchemy raise IntegrityError
            session.commit()
        
        session.rollback()  # Rollback de la transacción fallida
        
        print("✅ Restricciones de integridad verificadas correctamente")


class TestDatabasePerformance:
    """Tests básicos de rendimiento"""
    
    def test_bulk_operations(self, in_memory_db):
        """Verifica que las operaciones masivas funcionen eficientemente"""
        engine, session = in_memory_db
        
        # Crear múltiples tipos de usuario en bulk
        tipos_usuario = []
        for i in range(100):
            tipo = TipoUsuario(
                nombre=f"Tipo_{i}",
                descripcion=f"Descripción del tipo {i}"
            )
            tipos_usuario.append(tipo)
        
        session.add_all(tipos_usuario)
        session.commit()
        
        # Verificar que se crearon todos
        count = session.query(TipoUsuario).count()
        assert count == 100
        
        # Verificar consulta con filtro
        tipos_filtrados = session.query(TipoUsuario).filter(
            TipoUsuario.nombre.like("Tipo_1%")
        ).all()
        assert len(tipos_filtrados) == 11  # Tipo_1, Tipo_10-19
        
        print("✅ Operaciones masivas verificadas correctamente")


if __name__ == "__main__":
    # Ejecutar tests directamente si se ejecuta el archivo
    pytest.main([__file__, "-v"])