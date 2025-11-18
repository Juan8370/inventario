"""
Tests para los endpoints de la API con autenticación
"""
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
import sys
import os

# Agregar el directorio padre al path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.main import app
from app.src.database.database import get_db
from app.src.database.models import Base


# Configurar base de datos de prueba en memoria
TEST_DATABASE_URL = "sqlite:///:memory:"

engine = create_engine(
    TEST_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=__import__('sqlalchemy.pool', fromlist=['StaticPool']).StaticPool
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


# Override de la dependencia get_db para este módulo
def override_get_db_api():
    try:
        db = TestingSessionLocal()
        yield db
    finally:
        db.close()


# Cliente de prueba
client = TestClient(app)

# Aplicar override solo cuando se usen estos tests
app.dependency_overrides[get_db] = override_get_db_api


@pytest.fixture(scope="module")
def setup_database():
    """Crear las tablas antes de los tests y eliminarlas después"""
    # Asegurar que el override esté activo
    app.dependency_overrides[get_db] = override_get_db_api
    
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)
    engine.dispose()
    
    # Limpiar overrides al terminar
    if get_db in app.dependency_overrides:
        del app.dependency_overrides[get_db]


@pytest.fixture(scope="function")
def clean_database():
    """Limpiar datos entre tests"""
    db = TestingSessionLocal()
    try:
        # Eliminar datos de todas las tablas
        for table in reversed(Base.metadata.sorted_tables):
            db.execute(table.delete())
        db.commit()
    finally:
        db.close()
    yield


@pytest.fixture(scope="function")
def setup_test_users(setup_database, clean_database):
    """Crear usuarios de prueba para autenticación"""
    db = TestingSessionLocal()
    try:
        from app.src.database.models import Usuario, EstadoUsuario, TipoUsuario
        from app.src.auth.password import PasswordHandler
        
        password_handler = PasswordHandler()
        
        # Crear estado de usuario
        estado = EstadoUsuario(nombre="Activo", descripcion="Usuario activo", activo=True)
        db.add(estado)
        db.commit()
        db.refresh(estado)
        
        # Crear tipos de usuario
        tipo_admin = TipoUsuario(nombre="Administrador", descripcion="Tipo administrador")
        tipo_usuario = TipoUsuario(nombre="Usuario", descripcion="Tipo usuario")
        db.add_all([tipo_admin, tipo_usuario])
        db.commit()
        db.refresh(tipo_admin)
        db.refresh(tipo_usuario)
        
        # Crear usuario administrador
        admin = Usuario(
            nombre="Admin",
            apellido="Test",
            email="admin@test.com",
            username="admin",
            password_hash=password_handler.hash_password("admin123"),
            estado_usuario_id=estado.id,
            tipo_usuario_id=tipo_admin.id
        )
        db.add(admin)
        db.commit()
        db.refresh(admin)
        
        # Crear usuario normal
        user = Usuario(
            nombre="User",
            apellido="Test",
            email="user@test.com",
            username="user",
            password_hash=password_handler.hash_password("user123"),
            estado_usuario_id=estado.id,
            tipo_usuario_id=tipo_usuario.id
        )
        db.add(user)
        db.commit()
        db.refresh(user)
        
        return {
            "admin": {"email": "admin@test.com", "password": "admin123", "id": admin.id},
            "user": {"email": "user@test.com", "password": "user123", "id": user.id}
        }
    finally:
        db.close()


def get_auth_headers(email: str, password: str) -> dict:
    """Helper para obtener headers de autenticación"""
    login_data = {"email": email, "password": password}
    response = client.post("/auth/login", json=login_data)
    assert response.status_code == 200, f"Login failed: {response.json()}"
    token = response.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


class TestHealthEndpoints:
    """Tests para endpoints de salud y verificación"""
    
    def test_root_endpoint(self, setup_database):
        """Verificar endpoint raíz (público)"""
        response = client.get("/")
        assert response.status_code == 200
        data = response.json()
        assert "message" in data
        assert "version" in data
        assert "docs" in data
        print("✅ Endpoint raíz funciona correctamente")
    
    def test_health_check(self, setup_database):
        """Verificar endpoint de salud (público)"""
        response = client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "OK"
        assert "database" in data
        assert data["database"] == "conectada"
        print("✅ Health check funciona correctamente")
    
    def test_database_info_admin(self, setup_database, setup_test_users):
        """Verificar endpoint de información de BD (requiere admin)"""
        admin_headers = get_auth_headers(
            setup_test_users["admin"]["email"],
            setup_test_users["admin"]["password"]
        )
        
        response = client.get("/db/info", headers=admin_headers)
        assert response.status_code == 200
        data = response.json()
        assert "tables" in data
        assert "total_tables" in data
        assert data["total_tables"] > 0
        print("✅ Database info funciona correctamente")
    
    def test_database_info_unauthorized(self, setup_database, setup_test_users):
        """Verificar que database info rechaza usuarios no admin"""
        # Sin autenticación
        response = client.get("/db/info")
        assert response.status_code == 403  # FastAPI retorna 403 sin auth en este caso
        
        # Usuario normal (no admin)
        user_headers = get_auth_headers(
            setup_test_users["user"]["email"],
            setup_test_users["user"]["password"]
        )
        response = client.get("/db/info", headers=user_headers)
        assert response.status_code == 403
        print("✅ Database info rechaza correctamente usuarios no admin")
    
    def test_stats_endpoint(self, setup_database, setup_test_users):
        """Verificar endpoint de estadísticas (requiere autenticación)"""
        user_headers = get_auth_headers(
            setup_test_users["user"]["email"],
            setup_test_users["user"]["password"]
        )
        
        response = client.get("/stats", headers=user_headers)
        assert response.status_code == 200
        data = response.json()
        assert "total_productos" in data
        assert "total_empresas" in data
        assert "total_usuarios" in data
        assert data["database_connected"] == True
        print("✅ Stats endpoint funciona correctamente")
    
    def test_stats_unauthorized(self, setup_database):
        """Verificar que stats rechaza usuarios sin autenticación"""
        response = client.get("/stats")
        assert response.status_code == 403  # FastAPI retorna 403 sin auth
        print("✅ Stats rechaza correctamente sin autenticación")


class TestAuthEndpoints:
    """Tests para endpoints de autenticación"""
    
    def test_login_success(self, setup_database, setup_test_users):
        """Verificar login exitoso"""
        login_data = {
            "email": setup_test_users["user"]["email"],
            "password": setup_test_users["user"]["password"]
        }
        
        response = client.post("/auth/login", json=login_data)
        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert "token_type" in data
        assert data["token_type"] == "bearer"
        assert "user_id" in data
        print("✅ Login exitoso funciona correctamente")
    
    def test_login_wrong_password(self, setup_database, setup_test_users):
        """Verificar login con contraseña incorrecta"""
        login_data = {
            "email": setup_test_users["user"]["email"],
            "password": "wrongpassword"
        }
        
        response = client.post("/auth/login", json=login_data)
        assert response.status_code == 401
        assert "incorrectos" in response.json()["detail"]
        print("✅ Login rechaza contraseña incorrecta")
    
    def test_login_nonexistent_user(self, setup_database, clean_database):
        """Verificar login con usuario inexistente"""
        login_data = {
            "email": "noexiste@test.com",
            "password": "password123"
        }
        
        response = client.post("/auth/login", json=login_data)
        assert response.status_code == 401
        print("✅ Login rechaza usuario inexistente")
    
    def test_get_my_profile(self, setup_database, setup_test_users):
        """Verificar obtención de perfil del usuario autenticado"""
        user_headers = get_auth_headers(
            setup_test_users["user"]["email"],
            setup_test_users["user"]["password"]
        )
        
        response = client.get("/auth/me", headers=user_headers)
        assert response.status_code == 200
        data = response.json()
        assert data["email"] == setup_test_users["user"]["email"]
        assert data["username"] == "user"
        assert "password_hash" not in data
        print("✅ Obtener perfil funciona correctamente")
    
    def test_change_password(self, setup_database, setup_test_users):
        """Verificar cambio de contraseña"""
        user_headers = get_auth_headers(
            setup_test_users["user"]["email"],
            setup_test_users["user"]["password"]
        )
        
        change_data = {
            "current_password": setup_test_users["user"]["password"],
            "new_password": "newpassword123"
        }
        
        response = client.post("/auth/change-password", json=change_data, headers=user_headers)
        assert response.status_code == 200
        assert "actualizada" in response.json()["message"]
        
        # Verificar que puede hacer login con la nueva contraseña
        new_headers = get_auth_headers(
            setup_test_users["user"]["email"],
            "newpassword123"
        )
        assert new_headers is not None
        print("✅ Cambio de contraseña funciona correctamente")


class TestProductosEndpoints:
    """Tests para endpoints de productos"""
    
    @pytest.fixture
    def setup_producto_data(self, clean_database, setup_test_users):
        """Crear datos necesarios para productos"""
        db = TestingSessionLocal()
        try:
            from app.src.database.models import TipoProducto, EstadoProducto
            
            tipo = TipoProducto(nombre="Electrónicos", descripcion="Productos electrónicos")
            db.add(tipo)
            db.commit()
            db.refresh(tipo)
            
            estado = EstadoProducto(nombre="Disponible", descripcion="Producto disponible")
            db.add(estado)
            db.commit()
            db.refresh(estado)
            
            return {
                "tipo_producto_id": tipo.id, 
                "estado_producto_id": estado.id,
                "users": setup_test_users
            }
        finally:
            db.close()
    
    def test_listar_productos_sin_auth(self, setup_database, clean_database):
        """Verificar que listar productos funciona sin autenticación (opcional)"""
        response = client.get("/productos")
        assert response.status_code == 200
        assert isinstance(response.json(), list)
        print("✅ Listar productos sin auth funciona correctamente")
    
    def test_crear_producto_con_auth(self, setup_database, setup_producto_data):
        """Verificar creación de producto con autenticación"""
        user_headers = get_auth_headers(
            setup_producto_data["users"]["user"]["email"],
            setup_producto_data["users"]["user"]["password"]
        )
        
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
        
        response = client.post("/productos", json=producto_data, headers=user_headers)
        assert response.status_code == 201
        data = response.json()
        assert data["codigo"] == "PROD-001"
        assert data["nombre"] == "Laptop Test"
        print("✅ Crear producto con auth funciona correctamente")
    
    def test_crear_producto_sin_auth(self, setup_database, setup_producto_data):
        """Verificar que crear producto requiere autenticación"""
        producto_data = {
            "codigo": "PROD-002",
            "nombre": "Producto sin auth",
            "precio_compra": 100.00,
            "precio_venta": 150.00,
            "stock_minimo": 1,
            "tipo_producto_id": setup_producto_data["tipo_producto_id"],
            "estado_producto_id": setup_producto_data["estado_producto_id"]
        }
        
        response = client.post("/productos", json=producto_data)
        assert response.status_code == 403  # FastAPI retorna 403 sin auth
        print("✅ Crear producto rechaza sin autenticación")
    
    def test_actualizar_producto_con_auth(self, setup_database, setup_producto_data):
        """Verificar actualización de producto con autenticación"""
        user_headers = get_auth_headers(
            setup_producto_data["users"]["user"]["email"],
            setup_producto_data["users"]["user"]["password"]
        )
        
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
        
        create_response = client.post("/productos", json=producto_data, headers=user_headers)
        producto_id = create_response.json()["id"]
        
        # Actualizar producto
        update_data = {"nombre": "Producto Actualizado", "precio_venta": 175.00}
        response = client.put(f"/productos/{producto_id}", json=update_data, headers=user_headers)
        assert response.status_code == 200
        assert response.json()["nombre"] == "Producto Actualizado"
        print("✅ Actualizar producto con auth funciona correctamente")
    
    def test_eliminar_producto_requiere_admin(self, setup_database, setup_producto_data):
        """Verificar que eliminar producto requiere rol de administrador"""
        user_headers = get_auth_headers(
            setup_producto_data["users"]["user"]["email"],
            setup_producto_data["users"]["user"]["password"]
        )
        admin_headers = get_auth_headers(
            setup_producto_data["users"]["admin"]["email"],
            setup_producto_data["users"]["admin"]["password"]
        )
        
        # Crear producto con usuario normal
        producto_data = {
            "codigo": "PROD-DEL",
            "nombre": "Producto a eliminar",
            "precio_compra": 50.00,
            "precio_venta": 75.00,
            "stock_minimo": 1,
            "tipo_producto_id": setup_producto_data["tipo_producto_id"],
            "estado_producto_id": setup_producto_data["estado_producto_id"]
        }
        
        create_response = client.post("/productos", json=producto_data, headers=user_headers)
        producto_id = create_response.json()["id"]
        
        # Intentar eliminar con usuario normal (debe fallar)
        response = client.delete(f"/productos/{producto_id}", headers=user_headers)
        assert response.status_code == 403
        
        # Eliminar con admin (debe funcionar)
        response = client.delete(f"/productos/{producto_id}", headers=admin_headers)
        assert response.status_code == 200
        print("✅ Eliminar producto requiere admin correctamente")


class TestEmpresasEndpoints:
    """Tests para endpoints de empresas"""
    
    @pytest.fixture
    def setup_empresa_data(self, clean_database, setup_test_users):
        """Crear datos necesarios para empresas"""
        db = TestingSessionLocal()
        try:
            from app.src.database.models import TipoEmpresa, EstadoEmpresa
            
            tipo = TipoEmpresa(nombre="Cliente", descripcion="Empresa cliente")
            db.add(tipo)
            db.commit()
            db.refresh(tipo)
            
            estado = EstadoEmpresa(nombre="Activo", descripcion="Empresa activa")
            db.add(estado)
            db.commit()
            db.refresh(estado)
            
            return {
                "tipo_empresa_id": tipo.id, 
                "estado_empresa_id": estado.id,
                "users": setup_test_users
            }
        finally:
            db.close()
    
    def test_listar_empresas_requiere_auth(self, setup_database, setup_test_users):
        """Verificar que listar empresas requiere autenticación"""
        # Sin autenticación
        response = client.get("/empresas")
        assert response.status_code == 403  # FastAPI retorna 403 sin auth
        
        # Con autenticación
        user_headers = get_auth_headers(
            setup_test_users["user"]["email"],
            setup_test_users["user"]["password"]
        )
        response = client.get("/empresas", headers=user_headers)
        assert response.status_code == 200
        print("✅ Listar empresas requiere autenticación correctamente")
    
    def test_crear_empresa_requiere_admin(self, setup_database, setup_empresa_data):
        """Verificar que crear empresa requiere rol de administrador"""
        user_headers = get_auth_headers(
            setup_empresa_data["users"]["user"]["email"],
            setup_empresa_data["users"]["user"]["password"]
        )
        admin_headers = get_auth_headers(
            setup_empresa_data["users"]["admin"]["email"],
            setup_empresa_data["users"]["admin"]["password"]
        )
        
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
        
        # Intentar con usuario normal (debe fallar)
        response = client.post("/empresas", json=empresa_data, headers=user_headers)
        assert response.status_code == 403
        
        # Crear con admin (debe funcionar)
        response = client.post("/empresas", json=empresa_data, headers=admin_headers)
        assert response.status_code == 201
        assert response.json()["nombre"] == "Empresa Test S.A."
        print("✅ Crear empresa requiere admin correctamente")


class TestValidacionesYErrores:
    """Tests para validaciones y manejo de errores"""
    
    def test_token_invalido(self, setup_database):
        """Verificar rechazo de token inválido"""
        headers = {"Authorization": "Bearer tokeninvalido123"}
        response = client.get("/auth/me", headers=headers)
        assert response.status_code == 401
        print("✅ Token inválido rechazado correctamente")
    
    def test_token_malformado(self, setup_database):
        """Verificar rechazo de header malformado"""
        headers = {"Authorization": "InvalidFormat"}
        response = client.get("/auth/me", headers=headers)
        assert response.status_code == 403  # FastAPI retorna 403 para formato incorrecto
        print("✅ Token malformado rechazado correctamente")
    
    def test_endpoint_inexistente(self, setup_database):
        """Verificar error 404 en endpoint inexistente"""
        response = client.get("/endpoint/inexistente")
        assert response.status_code == 404
        print("✅ Endpoint inexistente retorna 404 correctamente")


class TestIntegracionCompleta:
    """Tests de integración de flujos completos"""
    
    def test_flujo_completo_usuario_y_productos(self, setup_database, setup_test_users):
        """Verificar flujo completo de autenticación y operaciones con productos"""
        db = TestingSessionLocal()
        try:
            from app.src.database.models import TipoProducto, EstadoProducto
            
            # Preparar datos
            tipo = TipoProducto(nombre="Test", descripcion="Test tipo")
            estado = EstadoProducto(nombre="Test", descripcion="Test estado")
            db.add_all([tipo, estado])
            db.commit()
            db.refresh(tipo)
            db.refresh(estado)
            
            # 1. Login
            login_data = {
                "email": setup_test_users["user"]["email"],
                "password": setup_test_users["user"]["password"]
            }
            login_response = client.post("/auth/login", json=login_data)
            assert login_response.status_code == 200
            token = login_response.json()["access_token"]
            headers = {"Authorization": f"Bearer {token}"}
            
            # 2. Obtener perfil
            profile_response = client.get("/auth/me", headers=headers)
            assert profile_response.status_code == 200
            
            # 3. Crear producto
            producto_data = {
                "codigo": "INT-001",
                "nombre": "Producto Integración",
                "precio_compra": 100.00,
                "precio_venta": 150.00,
                "stock_minimo": 5,
                "tipo_producto_id": tipo.id,
                "estado_producto_id": estado.id
            }
            create_response = client.post("/productos", json=producto_data, headers=headers)
            assert create_response.status_code == 201
            producto_id = create_response.json()["id"]
            
            # 4. Listar productos (sin autenticación)
            list_response = client.get("/productos")
            assert list_response.status_code == 200
            assert len(list_response.json()) == 1
            
            # 5. Obtener producto específico
            get_response = client.get(f"/productos/{producto_id}")
            assert get_response.status_code == 200
            
            # 6. Actualizar producto
            update_response = client.put(
                f"/productos/{producto_id}", 
                json={"nombre": "Producto Actualizado"},
                headers=headers
            )
            assert update_response.status_code == 200
            
            # 7. Intentar eliminar con usuario normal (debe fallar)
            delete_response = client.delete(f"/productos/{producto_id}", headers=headers)
            assert delete_response.status_code == 403
            
            # 8. Eliminar con admin
            admin_headers = get_auth_headers(
                setup_test_users["admin"]["email"],
                setup_test_users["admin"]["password"]
            )
            delete_response = client.delete(f"/productos/{producto_id}", headers=admin_headers)
            assert delete_response.status_code == 200
            
            print("✅ Flujo completo de integración funciona correctamente")
        finally:
            db.close()


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
