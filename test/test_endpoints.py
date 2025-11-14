import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
import sys
import os

# Agregar el directorio padre al path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.main import app
from app.database.database import get_db
from app.database.models import Base


# Configurar base de datos de prueba
TEST_DATABASE_URL = "sqlite:///./test_inventario.db"

engine = create_engine(
    TEST_DATABASE_URL,
    connect_args={"check_same_thread": False}
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


# Override de la dependencia get_db
def override_get_db():
    try:
        db = TestingSessionLocal()
        yield db
    finally:
        db.close()


app.dependency_overrides[get_db] = override_get_db

# Cliente de prueba
client = TestClient(app)


@pytest.fixture(scope="module")
def setup_database():
    """Crear las tablas antes de los tests y eliminarlas después"""
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)
    # Eliminar el archivo de base de datos de prueba
    # Asegurar liberar conexiones antes de borrar en Windows
    try:
        engine.dispose()
    except Exception:
        pass
    if os.path.exists("test_inventario.db"):
        os.remove("test_inventario.db")


@pytest.fixture(scope="function")
def clean_database():
    """Limpiar datos entre tests"""
    # Obtener todas las tablas
    db = TestingSessionLocal()
    try:
        # Eliminar datos de todas las tablas
        for table in reversed(Base.metadata.sorted_tables):
            db.execute(table.delete())
        db.commit()
    finally:
        db.close()
    yield


class TestHealthEndpoints:
    """Tests para endpoints de salud y verificación"""
    
    def test_root_endpoint(self, setup_database):
        """Verificar endpoint raíz"""
        response = client.get("/")
        assert response.status_code == 200
        data = response.json()
        assert "message" in data
        assert "version" in data
        assert "docs" in data
        print("✅ Endpoint raíz funciona correctamente")
    
    def test_health_check(self, setup_database):
        """Verificar endpoint de salud"""
        response = client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "OK"
        assert "database" in data
        assert data["database"] == "conectada"
        print("✅ Health check funciona correctamente")
    
    def test_database_info(self, setup_database):
        """Verificar endpoint de información de BD"""
        response = client.get("/db/info")
        assert response.status_code == 200
        data = response.json()
        assert "tables" in data
        assert "total_tables" in data
        assert data["total_tables"] > 0
        print("✅ Database info funciona correctamente")
    
    def test_stats_endpoint(self, setup_database, clean_database):
        """Verificar endpoint de estadísticas"""
        response = client.get("/stats")
        assert response.status_code == 200
        data = response.json()
        assert "total_productos" in data
        assert "total_empresas" in data
        assert "total_usuarios" in data
        assert data["database_connected"] == True
        print("✅ Stats endpoint funciona correctamente")


class TestProductosEndpoints:
    """Tests para endpoints de productos"""
    
    @pytest.fixture
    def setup_producto_data(self, clean_database):
        """Crear datos necesarios para productos"""
        db = TestingSessionLocal()
        try:
            from app.database.models import TipoProducto, EstadoProducto
            
            # Crear tipo de producto
            tipo = TipoProducto(nombre="Electrónicos", descripcion="Productos electrónicos")
            db.add(tipo)
            db.commit()
            db.refresh(tipo)
            
            # Crear estado de producto
            estado = EstadoProducto(nombre="Disponible", descripcion="Producto disponible")
            db.add(estado)
            db.commit()
            db.refresh(estado)
            
            return {"tipo_producto_id": tipo.id, "estado_producto_id": estado.id}
        finally:
            db.close()
    
    def test_listar_productos_vacio(self, setup_database, clean_database):
        """Verificar listado de productos cuando está vacío"""
        response = client.get("/productos")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) == 0
        print("✅ Listar productos vacío funciona correctamente")
    
    def test_crear_producto(self, setup_database, setup_producto_data):
        """Verificar creación de producto"""
        producto_data = {
            "codigo": "PROD-001",
            "nombre": "Laptop Test",
            "descripcion": "Laptop para testing",
            "marca": "TestBrand",
            "modelo": "X-1000",
            "precio_compra": 800.00,
            "precio_venta": 1000.00,
            "stock_minimo": 5,
            "unidad_medida": "pza",
            "tipo_producto_id": setup_producto_data["tipo_producto_id"],
            "estado_producto_id": setup_producto_data["estado_producto_id"]
        }
        
        response = client.post("/productos", json=producto_data)
        assert response.status_code == 201
        data = response.json()
        assert data["codigo"] == "PROD-001"
        assert data["nombre"] == "Laptop Test"
        assert "id" in data
        print("✅ Crear producto funciona correctamente")
    
    def test_crear_producto_duplicado(self, setup_database, setup_producto_data):
        """Verificar que no se puedan crear productos con código duplicado"""
        producto_data = {
            "codigo": "PROD-DUP",
            "nombre": "Producto Original",
            "precio_compra": 100.00,
            "precio_venta": 150.00,
            "stock_minimo": 1,
            "tipo_producto_id": setup_producto_data["tipo_producto_id"],
            "estado_producto_id": setup_producto_data["estado_producto_id"]
        }
        
        # Crear primer producto
        response = client.post("/productos", json=producto_data)
        assert response.status_code == 201
        
        # Intentar crear producto duplicado
        response = client.post("/productos", json=producto_data)
        assert response.status_code == 400
        assert "Ya existe un producto con este código" in response.json()["detail"]
        print("✅ Validación de código duplicado funciona correctamente")
    
    def test_obtener_producto(self, setup_database, setup_producto_data):
        """Verificar obtención de producto por ID"""
        # Crear producto
        producto_data = {
            "codigo": "PROD-GET",
            "nombre": "Producto para obtener",
            "precio_compra": 50.00,
            "precio_venta": 75.00,
            "stock_minimo": 2,
            "tipo_producto_id": setup_producto_data["tipo_producto_id"],
            "estado_producto_id": setup_producto_data["estado_producto_id"]
        }
        
        create_response = client.post("/productos", json=producto_data)
        producto_id = create_response.json()["id"]
        
        # Obtener producto
        response = client.get(f"/productos/{producto_id}")
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == producto_id
        assert data["codigo"] == "PROD-GET"
        print("✅ Obtener producto funciona correctamente")
    
    def test_obtener_producto_inexistente(self, setup_database, clean_database):
        """Verificar error al obtener producto inexistente"""
        response = client.get("/productos/99999")
        assert response.status_code == 404
        assert "no encontrado" in response.json()["detail"]
        print("✅ Error 404 para producto inexistente funciona correctamente")
    
    def test_actualizar_producto(self, setup_database, setup_producto_data):
        """Verificar actualización de producto"""
        # Crear producto
        producto_data = {
            "codigo": "PROD-UPD",
            "nombre": "Producto Original",
            "precio_compra": 100.00,
            "precio_venta": 150.00,
            "stock_minimo": 5,
            "tipo_producto_id": setup_producto_data["tipo_producto_id"],
            "estado_producto_id": setup_producto_data["estado_producto_id"]
        }
        
        create_response = client.post("/productos", json=producto_data)
        producto_id = create_response.json()["id"]
        
        # Actualizar producto
        update_data = {
            "nombre": "Producto Actualizado",
            "precio_venta": 175.00
        }
        
        response = client.put(f"/productos/{producto_id}", json=update_data)
        assert response.status_code == 200
        data = response.json()
        assert data["nombre"] == "Producto Actualizado"
        assert data["precio_venta"] == 175.00
        print("✅ Actualizar producto funciona correctamente")
    
    def test_eliminar_producto(self, setup_database, setup_producto_data):
        """Verificar eliminación de producto"""
        # Crear producto
        producto_data = {
            "codigo": "PROD-DEL",
            "nombre": "Producto a eliminar",
            "precio_compra": 50.00,
            "precio_venta": 75.00,
            "stock_minimo": 1,
            "tipo_producto_id": setup_producto_data["tipo_producto_id"],
            "estado_producto_id": setup_producto_data["estado_producto_id"]
        }
        
        create_response = client.post("/productos", json=producto_data)
        producto_id = create_response.json()["id"]
        
        # Eliminar producto
        response = client.delete(f"/productos/{producto_id}")
        assert response.status_code == 200
        assert "eliminado correctamente" in response.json()["message"]
        
        # Verificar que ya no existe
        get_response = client.get(f"/productos/{producto_id}")
        assert get_response.status_code == 404
        print("✅ Eliminar producto funciona correctamente")
    
    def test_buscar_productos(self, setup_database, setup_producto_data):
        """Verificar búsqueda de productos"""
        # Crear varios productos
        productos = [
            {"codigo": "LAP-001", "nombre": "Laptop Dell", "marca": "Dell"},
            {"codigo": "LAP-002", "nombre": "Laptop HP", "marca": "HP"},
            {"codigo": "MOUSE-001", "nombre": "Mouse Logitech", "marca": "Logitech"}
        ]
        
        for prod in productos:
            producto_data = {
                **prod,
                "precio_compra": 100.00,
                "precio_venta": 150.00,
                "stock_minimo": 1,
                "tipo_producto_id": setup_producto_data["tipo_producto_id"],
                "estado_producto_id": setup_producto_data["estado_producto_id"]
            }
            client.post("/productos", json=producto_data)
        
        # Buscar por término "Laptop"
        response = client.get("/productos/buscar/Laptop")
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 2
        assert all("Laptop" in p["nombre"] for p in data)
        print("✅ Búsqueda de productos funciona correctamente")
    
    def test_listar_productos_con_paginacion(self, setup_database, setup_producto_data):
        """Verificar paginación en listado de productos"""
        # Crear 15 productos
        for i in range(15):
            producto_data = {
                "codigo": f"PROD-{i:03d}",
                "nombre": f"Producto {i}",
                "precio_compra": 100.00,
                "precio_venta": 150.00,
                "stock_minimo": 1,
                "tipo_producto_id": setup_producto_data["tipo_producto_id"],
                "estado_producto_id": setup_producto_data["estado_producto_id"]
            }
            client.post("/productos", json=producto_data)
        
        # Obtener primera página (skip=0, limit=10)
        response = client.get("/productos?skip=0&limit=10")
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 10
        
        # Obtener segunda página (skip=10, limit=10)
        response = client.get("/productos?skip=10&limit=10")
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 5
        print("✅ Paginación funciona correctamente")


class TestEmpresasEndpoints:
    """Tests para endpoints de empresas"""
    
    @pytest.fixture
    def setup_empresa_data(self, clean_database):
        """Crear datos necesarios para empresas"""
        db = TestingSessionLocal()
        try:
            from app.database.models import TipoEmpresa, EstadoEmpresa
            
            tipo = TipoEmpresa(nombre="Cliente", descripcion="Empresa cliente")
            db.add(tipo)
            db.commit()
            db.refresh(tipo)
            
            estado = EstadoEmpresa(nombre="Activo", descripcion="Empresa activa")
            db.add(estado)
            db.commit()
            db.refresh(estado)
            
            return {"tipo_empresa_id": tipo.id, "estado_empresa_id": estado.id}
        finally:
            db.close()
    
    def test_listar_empresas_vacio(self, setup_database, clean_database):
        """Verificar listado de empresas cuando está vacío"""
        response = client.get("/empresas")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) == 0
        print("✅ Listar empresas vacío funciona correctamente")
    
    def test_crear_empresa(self, setup_database, setup_empresa_data):
        """Verificar creación de empresa"""
        empresa_data = {
            "nombre": "Empresa Test S.A.",
            "ruc": "20123456789",
            "direccion": "Av. Test 123",
            "telefono": "555-1234",
            "email": "contacto@empresatest.com",
            "contacto_principal": "Juan Pérez",
            "tipo_empresa_id": setup_empresa_data["tipo_empresa_id"],
            "estado_empresa_id": setup_empresa_data["estado_empresa_id"]
        }
        
        response = client.post("/empresas", json=empresa_data)
        assert response.status_code == 201
        data = response.json()
        assert data["nombre"] == "Empresa Test S.A."
        assert data["ruc"] == "20123456789"
        assert "id" in data
        print("✅ Crear empresa funciona correctamente")
    
    def test_crear_empresa_ruc_duplicado(self, setup_database, setup_empresa_data):
        """Verificar que no se puedan crear empresas con RUC duplicado"""
        empresa_data = {
            "nombre": "Empresa Original",
            "ruc": "20999999999",
            "tipo_empresa_id": setup_empresa_data["tipo_empresa_id"],
            "estado_empresa_id": setup_empresa_data["estado_empresa_id"]
        }
        
        # Crear primera empresa
        response = client.post("/empresas", json=empresa_data)
        assert response.status_code == 201
        
        # Intentar crear empresa con RUC duplicado
        empresa_data["nombre"] = "Empresa Duplicada"
        response = client.post("/empresas", json=empresa_data)
        assert response.status_code == 400
        assert "Ya existe una empresa con este RUC" in response.json()["detail"]
        print("✅ Validación de RUC duplicado funciona correctamente")


class TestValidaciones:
    """Tests para validaciones de datos"""
    
    def test_producto_datos_invalidos(self, setup_database, clean_database):
        """Verificar que se rechacen datos inválidos"""
        producto_data = {
            "codigo": "",  # Código vacío (inválido)
            "nombre": "Test",
            "tipo_producto_id": 1,
            "estado_producto_id": 1
        }
        
        response = client.post("/productos", json=producto_data)
        assert response.status_code == 422  # Unprocessable Entity
        print("✅ Validación de datos inválidos funciona correctamente")
    
    def test_paginacion_parametros_invalidos(self, setup_database, clean_database):
        """Verificar manejo de parámetros de paginación inválidos"""
        # Skip negativo
        response = client.get("/productos?skip=-1&limit=10")
        assert response.status_code == 422
        
        # Limit negativo
        response = client.get("/productos?skip=0&limit=-5")
        assert response.status_code == 422
        print("✅ Validación de parámetros de paginación funciona correctamente")


class TestIntegracion:
    """Tests de integración de flujos completos"""
    
    def test_flujo_completo_producto(self, setup_database, clean_database):
        """Verificar flujo completo: crear, listar, obtener, actualizar, eliminar"""
        db = TestingSessionLocal()
        try:
            from app.database.models import TipoProducto, EstadoProducto
            
            # Preparar datos
            tipo = TipoProducto(nombre="Test", descripcion="Test tipo")
            estado = EstadoProducto(nombre="Test", descripcion="Test estado")
            db.add_all([tipo, estado])
            db.commit()
            db.refresh(tipo)
            db.refresh(estado)
            
            # 1. Crear producto
            producto_data = {
                "codigo": "INT-001",
                "nombre": "Producto Integración",
                "precio_compra": 100.00,
                "precio_venta": 150.00,
                "stock_minimo": 5,
                "tipo_producto_id": tipo.id,
                "estado_producto_id": estado.id
            }
            
            create_response = client.post("/productos", json=producto_data)
            assert create_response.status_code == 201
            producto_id = create_response.json()["id"]
            
            # 2. Listar productos
            list_response = client.get("/productos")
            assert list_response.status_code == 200
            assert len(list_response.json()) == 1
            
            # 3. Obtener producto específico
            get_response = client.get(f"/productos/{producto_id}")
            assert get_response.status_code == 200
            assert get_response.json()["codigo"] == "INT-001"
            
            # 4. Actualizar producto
            update_data = {"nombre": "Producto Actualizado"}
            update_response = client.put(f"/productos/{producto_id}", json=update_data)
            assert update_response.status_code == 200
            assert update_response.json()["nombre"] == "Producto Actualizado"
            
            # 5. Buscar producto
            search_response = client.get("/productos/buscar/Actualizado")
            assert search_response.status_code == 200
            assert len(search_response.json()) == 1
            
            # 6. Eliminar producto
            delete_response = client.delete(f"/productos/{producto_id}")
            assert delete_response.status_code == 200
            
            # 7. Verificar que fue eliminado
            get_response = client.get(f"/productos/{producto_id}")
            assert get_response.status_code == 404
            
            print("✅ Flujo completo de producto funciona correctamente")
        finally:
            db.close()


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
