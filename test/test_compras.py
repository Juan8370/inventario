"""
Tests para el módulo de Compras:
- Crear cabecera de compra
- Agregar items (batch) como transacciones ENTRADA
- Validar inventario actualizado
- Listar compras e items
"""
import pytest
import sys
import os
from datetime import datetime

from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

# Agregar el directorio raíz al path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.main import app
from app.src.database.database import get_db
from app.src.database.models import Base, TipoTransaccion, TipoProducto, EstadoProducto


# Base de datos de prueba en memoria (compartida)
TEST_DATABASE_URL = "sqlite:///:memory:"
engine = create_engine(
    TEST_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=__import__('sqlalchemy.pool', fromlist=['StaticPool']).StaticPool
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


# Override de la dependencia get_db
def override_get_db():
    try:
        db = TestingSessionLocal()
        yield db
    finally:
        db.close()


# Cliente de prueba
client = TestClient(app)
app.dependency_overrides[get_db] = override_get_db


@pytest.fixture(scope="module")
def setup_database():
    """Crear tablas antes de los tests y eliminarlas después"""
    app.dependency_overrides[get_db] = override_get_db
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)
    engine.dispose()
    if get_db in app.dependency_overrides:
        del app.dependency_overrides[get_db]


@pytest.fixture(scope="function")
def clean_database():
    """Limpiar datos entre tests"""
    db = TestingSessionLocal()
    try:
        for table in reversed(Base.metadata.sorted_tables):
            db.execute(table.delete())
        db.commit()
    finally:
        db.close()
    yield


@pytest.fixture(scope="function")
def setup_test_users(setup_database, clean_database):
    """Crear usuarios y datos básicos para autenticación"""
    db = TestingSessionLocal()
    try:
        from app.src.database.models import Usuario, EstadoUsuario, TipoUsuario
        from app.src.auth.password import PasswordHandler

        password_handler = PasswordHandler()

        # Estados y tipos
        estado = EstadoUsuario(nombre="Activo", descripcion="Usuario activo", activo=True)
        db.add(estado); db.commit(); db.refresh(estado)

        tipo_admin = TipoUsuario(nombre="Administrador", descripcion="Admin")
        tipo_usuario = TipoUsuario(nombre="Usuario", descripcion="Usuario")
        db.add_all([tipo_admin, tipo_usuario]); db.commit(); db.refresh(tipo_admin); db.refresh(tipo_usuario)

        # Usuarios
        admin = Usuario(
            nombre="Admin", apellido="Test", email="admin@test.com", username="admin",
            password_hash=password_handler.hash_password("admin123"),
            estado_usuario_id=estado.id, tipo_usuario_id=tipo_admin.id
        )
        user = Usuario(
            nombre="User", apellido="Test", email="user@test.com", username="user",
            password_hash=password_handler.hash_password("user123"),
            estado_usuario_id=estado.id, tipo_usuario_id=tipo_usuario.id
        )
        db.add_all([admin, user]); db.commit(); db.refresh(admin); db.refresh(user)

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


@pytest.fixture(scope="function")
def setup_productos_y_tipos(setup_database):
    """Crea TipoTransaccion ENTRADA, y tipos/estados de producto para las pruebas"""
    db = TestingSessionLocal()
    try:
        # Tipos de transacción necesarios
        if not db.query(TipoTransaccion).filter(TipoTransaccion.nombre == "ENTRADA").first():
            db.add(TipoTransaccion(nombre="ENTRADA", descripcion="Entrada de productos"))
            db.commit()
        if not db.query(TipoTransaccion).filter(TipoTransaccion.nombre == "SALIDA").first():
            db.add(TipoTransaccion(nombre="SALIDA", descripcion="Salida de productos"))
            db.commit()

        # Tipos/Estados de producto
        if not db.query(TipoProducto).first():
            db.add(TipoProducto(nombre="General", descripcion="General")); db.commit()
        if not db.query(EstadoProducto).first():
            db.add(EstadoProducto(nombre="Activo", descripcion="Activo")); db.commit()
    finally:
        db.close()
    yield


class TestComprasEndpoints:
    def test_crear_compra_header(self, setup_database, clean_database, setup_test_users, setup_productos_y_tipos):
        headers = get_auth_headers(setup_test_users["user"]["email"], setup_test_users["user"]["password"])
        payload = {
            "numero_compra": "C-0001",
            "proveedor_id": 123,
            "tienda": "Central",
            "subtotal": 100.00,
            "impuesto": 18.00,
            "descuento": 10.00,
            "observaciones": "Compra inicial"
        }
        resp = client.post("/compras/", json=payload, headers=headers)
        assert resp.status_code == 201, resp.text
        data = resp.json()
        assert data["numero_compra"] == "C-0001"
        assert data["proveedor_id"] == 123
        # total = 100 + 18 - 10 = 108
        assert float(data["total"]) == 108.0

    def test_agregar_items_y_actualizar_inventario(self, setup_database, clean_database, setup_test_users, setup_productos_y_tipos):
        # Login
        headers = get_auth_headers(setup_test_users["user"]["email"], setup_test_users["user"]["password"])

        # Crear tipos/estados y producto
        db = TestingSessionLocal()
        try:
            tipo = db.query(TipoProducto).first()
            estado = db.query(EstadoProducto).first()
        finally:
            db.close()

        producto_payload = {
            "codigo": "PROD-COMP-1",
            "nombre": "Producto Compra",
            "precio_compra": 10.00,
            "precio_venta": 15.00,
            "stock_minimo": 1,
            "tipo_producto_id": tipo.id,
            "estado_producto_id": estado.id
        }
        prod_resp = client.post("/productos", json=producto_payload, headers=headers)
        assert prod_resp.status_code == 201, prod_resp.text
        producto_id = prod_resp.json()["id"]

        # Crear compra
        compra_resp = client.post("/compras/", json={"numero_compra": "C-0002", "subtotal": 0, "impuesto": 0, "descuento": 0}, headers=headers)
        assert compra_resp.status_code == 201, compra_resp.text
        compra_id = compra_resp.json()["id"]

        # Agregar items (batch)
        items_payload = {
            "items": [
                {"producto_id": producto_id, "cantidad": 5, "observaciones": "Lote 1"},
                {"producto_id": producto_id, "cantidad": 3}
            ]
        }
        items_resp = client.post(f"/compras/{compra_id}/transacciones", json=items_payload, headers=headers)
        assert items_resp.status_code == 201, items_resp.text
        trans = items_resp.json()
        assert len(trans) == 2
        assert all(t["compra_id"] == compra_id for t in trans)
        assert all(t["producto_id"] == producto_id for t in trans)

        # Verificar stock (5 + 3)
        stock_resp = client.get(f"/transacciones/stock/{producto_id}", headers=headers)
        assert stock_resp.status_code == 200, stock_resp.text
        stock_data = stock_resp.json()
        assert stock_data["stock_actual"] == 8.0
        assert stock_data["bajo_stock"] is False

    def test_listar_items_compra(self, setup_database, clean_database, setup_test_users, setup_productos_y_tipos):
        headers = get_auth_headers(setup_test_users["user"]["email"], setup_test_users["user"]["password"])

        # Preparar producto
        db = TestingSessionLocal()
        try:
            tipo = db.query(TipoProducto).first()
            estado = db.query(EstadoProducto).first()
        finally:
            db.close()
        prod = {
            "codigo": "PROD-COMP-2",
            "nombre": "Prod 2",
            "precio_compra": 5.00,
            "precio_venta": 9.00,
            "stock_minimo": 1,
            "tipo_producto_id": tipo.id,
            "estado_producto_id": estado.id
        }
        prod_resp = client.post("/productos", json=prod, headers=headers)
        producto_id = prod_resp.json()["id"]

        # Crear compra y agregar items
        compra_id = client.post("/compras/", json={"numero_compra": "C-0003", "subtotal": 0, "impuesto": 0, "descuento": 0}, headers=headers).json()["id"]
        client.post(f"/compras/{compra_id}/transacciones", json={"items": [{"producto_id": producto_id, "cantidad": 2}, {"producto_id": producto_id, "cantidad": 1}]}, headers=headers)

        # Listar items
        list_resp = client.get(f"/compras/{compra_id}/transacciones", headers=headers)
        assert list_resp.status_code == 200
        items = list_resp.json()
        assert len(items) == 2
        assert all(i["compra_id"] == compra_id for i in items)

    def test_listar_compras_filtrado_numero(self, setup_database, clean_database, setup_test_users, setup_productos_y_tipos):
        headers = get_auth_headers(setup_test_users["user"]["email"], setup_test_users["user"]["password"])

        # Crear dos compras
        client.post("/compras/", json={"numero_compra": "FILTRO-1", "subtotal": 10, "impuesto": 0, "descuento": 0}, headers=headers)
        client.post("/compras/", json={"numero_compra": "FILTRO-2", "subtotal": 10, "impuesto": 0, "descuento": 0}, headers=headers)

        # Filtrar por numero
        list_resp = client.get("/compras?numero=FILTRO-2", headers=headers)
        assert list_resp.status_code == 200
        compras = list_resp.json()
        assert len(compras) == 1
        assert compras[0]["numero_compra"] == "FILTRO-2"
