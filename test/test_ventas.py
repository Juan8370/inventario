"""
Tests para el módulo de Ventas:
- Crear venta con detalles
- Asociar a cliente
- Descontar inventario
- Validar stock suficiente
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
from app.src.database.models import Base, TipoTransaccion, TipoProducto, EstadoProducto, EstadoVenta


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
    """Crea TipoTransaccion SALIDA, y tipos/estados de producto para las pruebas"""
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
        if not db.query(EstadoVenta).first():
            db.add(EstadoVenta(nombre="Procesada", descripcion="Venta procesada")); db.commit()
    finally:
        db.close()
    yield


class TestVentasEndpoints:
    """Tests para endpoints de ventas"""

    def test_crear_venta_con_detalles_y_actualizar_inventario(self, setup_database, clean_database, setup_test_users, setup_productos_y_tipos):
        """Prueba crear venta con detalles y verificar descuento de inventario"""
        headers = get_auth_headers(setup_test_users["user"]["email"], setup_test_users["user"]["password"])

        # Crear cliente
        cliente_data = {
            "nombre": "Cliente",
            "apellido": "Prueba",
            "identidad": "12345678",
            "telefono": "555-9999",
            "email": "cliente@test.com"
        }
        cliente_response = client.post("/clientes/", json=cliente_data, headers=headers)
        assert cliente_response.status_code == 201
        cliente_id = cliente_response.json()["id"]

        # Crear producto y inventario
        db = TestingSessionLocal()
        try:
            tipo_prod = db.query(TipoProducto).first()
            estado_prod = db.query(EstadoProducto).first()
        finally:
            db.close()

        producto_data = {
            "codigo": "PROD-VENTA",
            "nombre": "Producto Venta",
            "precio_venta": 100.00,
            "tipo_producto_id": tipo_prod.id,
            "estado_producto_id": estado_prod.id
        }
        producto_response = client.post("/productos", json=producto_data, headers=headers)
        assert producto_response.status_code == 201
        producto_id = producto_response.json()["id"]

        # Obtener ID de tipo ENTRADA
        db = TestingSessionLocal()
        try:
            tipo_entrada = db.query(TipoTransaccion).filter(TipoTransaccion.nombre == "ENTRADA").first()
            tipo_entrada_id = tipo_entrada.id
        finally:
            db.close()

        # Agregar inventario inicial (10 unidades) via Transacción
        transaccion_data = {
            "tipo_transaccion_id": tipo_entrada_id,
            "producto_id": producto_id,
            "cantidad": 10,
            "fecha": datetime.utcnow().isoformat(),
            "observaciones": "Inventario inicial"
        }
        client.post("/transacciones/", json=transaccion_data, headers=headers)

        # Obtener estado venta
        db = TestingSessionLocal()
        try:
            estado_venta = db.query(EstadoVenta).first()
        finally:
            db.close()

        # Crear venta con detalles
        venta_data = {
            "factura_id": "V-TEST-001",
            "cliente_id": cliente_id,
            "fecha": datetime.utcnow().isoformat(),
            "valor_total": 200.00,
            "estado_venta_id": estado_venta.id,
            "observaciones": "Venta de prueba",
            "detalle_ventas": [
                {
                    "producto_id": producto_id,
                    "cantidad": 2,
                    "precio_unitario": 100.00,
                    "descuento_unitario": 0.00,
                    "subtotal": 200.00
                }
            ]
        }

        response = client.post("/ventas/", json=venta_data, headers=headers)
        assert response.status_code == 201

        venta = response.json()
        assert venta["factura_id"] == "V-TEST-001"
        assert venta["cliente"]["id"] == cliente_id
        assert len(venta["detalle_ventas"]) == 1

        # Verificar que se creó la transacción SALIDA
        transacciones = client.get("/transacciones/", headers=headers).json()
        salidas = [t for t in transacciones if t["tipo_transaccion"]["nombre"] == "SALIDA" and t["venta_id"] == venta["id"]]
        assert len(salidas) == 1
        assert float(salidas[0]["cantidad"]) == 2.0

        # Verificar descuento de inventario
        stock_resp = client.get(f"/transacciones/stock/{producto_id}", headers=headers)
        assert stock_resp.status_code == 200
        stock_data = stock_resp.json()
        assert stock_data["stock_actual"] == 8.0

    def test_crear_venta_stock_insuficiente(self, setup_database, clean_database, setup_test_users, setup_productos_y_tipos):
        """Prueba error cuando no hay stock suficiente"""
        headers = get_auth_headers(setup_test_users["user"]["email"], setup_test_users["user"]["password"])

        # Crear cliente
        cliente_data = {
            "nombre": "Cliente",
            "apellido": "Prueba",
            "identidad": "87654321",
            "telefono": "555-9999",
            "email": "cliente2@test.com"
        }
        cliente_response = client.post("/clientes/", json=cliente_data, headers=headers)
        cliente_id = cliente_response.json()["id"]

        # Crear producto con poco stock
        db = TestingSessionLocal()
        try:
            tipo_prod = db.query(TipoProducto).first()
            estado_prod = db.query(EstadoProducto).first()
        finally:
            db.close()

        producto_data = {
            "codigo": "PROD-STOCK",
            "nombre": "Producto Stock",
            "precio_venta": 50.00,
            "tipo_producto_id": tipo_prod.id,
            "estado_producto_id": estado_prod.id
        }
        producto_response = client.post("/productos", json=producto_data, headers=headers)
        producto_id = producto_response.json()["id"]

        # Obtener ID de tipo ENTRADA
        db = TestingSessionLocal()
        try:
            tipo_entrada = db.query(TipoTransaccion).filter(TipoTransaccion.nombre == "ENTRADA").first()
            tipo_entrada_id = tipo_entrada.id
        finally:
            db.close()

        # Agregar inventario inicial (1 unidad) via Transacción
        transaccion_data = {
            "tipo_transaccion_id": tipo_entrada_id,
            "producto_id": producto_id,
            "cantidad": 1,
            "fecha": datetime.utcnow().isoformat(),
            "observaciones": "Inventario inicial"
        }
        client.post("/transacciones/", json=transaccion_data, headers=headers)

        # Obtener estado venta
        db = TestingSessionLocal()
        try:
            estado_venta = db.query(EstadoVenta).first()
        finally:
            db.close()

        # Intentar vender 5 unidades (más que disponible)
        venta_data = {
            "factura_id": "V-TEST-002",
            "cliente_id": cliente_id,
            "fecha": datetime.utcnow().isoformat(),
            "valor_total": 250.00,
            "estado_venta_id": estado_venta.id,
            "detalle_ventas": [
                {
                    "producto_id": producto_id,
                    "cantidad": 5,
                    "precio_unitario": 50.00,
                    "descuento_unitario": 0.00,
                    "subtotal": 250.00
                }
            ]
        }

        response = client.post("/ventas/", json=venta_data, headers=headers)
        assert response.status_code == 400
        assert "Stock insuficiente" in response.json()["detail"]

    def test_listar_ventas(self, setup_database, clean_database, setup_test_users, setup_productos_y_tipos):
        """Prueba listar ventas"""
        headers = get_auth_headers(setup_test_users["user"]["email"], setup_test_users["user"]["password"])
        response = client.get("/ventas/", headers=headers)
        assert response.status_code == 200
        assert isinstance(response.json(), list)

    def test_obtener_venta(self, setup_database, clean_database, setup_test_users, setup_productos_y_tipos):
        """Prueba obtener venta específica"""
        headers = get_auth_headers(setup_test_users["user"]["email"], setup_test_users["user"]["password"])

        # Crear venta primero
        # Crear cliente
        cliente_data = {
            "nombre": "Cliente",
            "apellido": "Test",
            "identidad": "11111111",
            "telefono": "555-1111",
            "email": "cliente3@test.com"
        }
        cliente_response = client.post("/clientes/", json=cliente_data, headers=headers)
        cliente_id = cliente_response.json()["id"]

        # Crear producto
        db = TestingSessionLocal()
        try:
            tipo_prod = db.query(TipoProducto).first()
            estado_prod = db.query(EstadoProducto).first()
        finally:
            db.close()

        producto_data = {
            "codigo": "PROD-TEST",
            "nombre": "Producto Test",
            "precio_venta": 100.00,
            "tipo_producto_id": tipo_prod.id,
            "estado_producto_id": estado_prod.id
        }
        producto_response = client.post("/productos", json=producto_data, headers=headers)
        producto_id = producto_response.json()["id"]

        # Obtener ID de tipo ENTRADA
        db = TestingSessionLocal()
        try:
            tipo_entrada = db.query(TipoTransaccion).filter(TipoTransaccion.nombre == "ENTRADA").first()
            tipo_entrada_id = tipo_entrada.id
        finally:
            db.close()

        # Agregar inventario via Transacción
        transaccion_data = {
            "tipo_transaccion_id": tipo_entrada_id,
            "producto_id": producto_id,
            "cantidad": 10,
            "fecha": datetime.utcnow().isoformat(),
            "observaciones": "Inventario inicial"
        }
        client.post("/transacciones/", json=transaccion_data, headers=headers)

        # Obtener estado venta
        db = TestingSessionLocal()
        try:
            estado_venta = db.query(EstadoVenta).first()
        finally:
            db.close()

        venta_data = {
            "factura_id": "V-TEST-003",
            "cliente_id": cliente_id,
            "fecha": datetime.utcnow().isoformat(),
            "valor_total": 100.00,
            "estado_venta_id": estado_venta.id,
            "detalle_ventas": [
                {
                    "producto_id": producto_id,
                    "cantidad": 1,
                    "precio_unitario": 100.00,
                    "descuento_unitario": 0.00,
                    "subtotal": 100.00
                }
            ]
        }

        create_response = client.post("/ventas/", json=venta_data, headers=headers)
        venta_id = create_response.json()["id"]

        # Obtener la venta
        response = client.get(f"/ventas/{venta_id}", headers=headers)
        assert response.status_code == 200
        assert response.json()["id"] == venta_id

    def test_listar_detalles_venta(self, setup_database, clean_database, setup_test_users, setup_productos_y_tipos):
        """Prueba listar detalles de una venta"""
        headers = get_auth_headers(setup_test_users["user"]["email"], setup_test_users["user"]["password"])

        # Crear venta primero
        # Crear cliente
        cliente_data = {
            "nombre": "Cliente",
            "apellido": "Detalles",
            "identidad": "22222222",
            "telefono": "555-2222",
            "email": "cliente4@test.com"
        }
        cliente_response = client.post("/clientes/", json=cliente_data, headers=headers)
        cliente_id = cliente_response.json()["id"]

        # Crear producto
        db = TestingSessionLocal()
        try:
            tipo_prod = db.query(TipoProducto).first()
            estado_prod = db.query(EstadoProducto).first()
        finally:
            db.close()

        producto_data = {
            "codigo": "PROD-DET",
            "nombre": "Producto Detalles",
            "precio_venta": 50.00,
            "tipo_producto_id": tipo_prod.id,
            "estado_producto_id": estado_prod.id
        }
        producto_response = client.post("/productos", json=producto_data, headers=headers)
        producto_id = producto_response.json()["id"]

        # Obtener ID de tipo ENTRADA
        db = TestingSessionLocal()
        try:
            tipo_entrada = db.query(TipoTransaccion).filter(TipoTransaccion.nombre == "ENTRADA").first()
            tipo_entrada_id = tipo_entrada.id
        finally:
            db.close()

        # Agregar inventario via Transacción
        transaccion_data = {
            "tipo_transaccion_id": tipo_entrada_id,
            "producto_id": producto_id,
            "cantidad": 10,
            "fecha": datetime.utcnow().isoformat(),
            "observaciones": "Inventario inicial"
        }
        client.post("/transacciones/", json=transaccion_data, headers=headers)

        # Obtener estado venta
        db = TestingSessionLocal()
        try:
            estado_venta = db.query(EstadoVenta).first()
        finally:
            db.close()

        venta_data = {
            "factura_id": "V-TEST-004",
            "cliente_id": cliente_id,
            "fecha": datetime.utcnow().isoformat(),
            "valor_total": 200.00,
            "estado_venta_id": estado_venta.id,
            "detalle_ventas": [
                {
                    "producto_id": producto_id,
                    "cantidad": 2,
                    "precio_unitario": 100.00,
                    "descuento_unitario": 0.00,
                    "subtotal": 200.00
                }
            ]
        }

        create_response = client.post("/ventas/", json=venta_data, headers=headers)
        venta_id = create_response.json()["id"]

        # Listar detalles
        response = client.get(f"/ventas/{venta_id}/detalles", headers=headers)
        assert response.status_code == 200
        assert len(response.json()) == 1