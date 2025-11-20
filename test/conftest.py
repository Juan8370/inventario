"""
Configuración global de pytest para los tests
"""
import pytest
import sys
import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

# Agregar el directorio raíz al path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.src.database.models import Base
from app.src.database.models import Base, TipoUsuario, EstadoUsuario, TipoProducto, EstadoProducto, Usuario
from app.src.database import crud, schemas
from app.src.auth import crud_usuario
from decimal import Decimal


def pytest_configure(config):
    """Configuración inicial de pytest"""
    config.addinivalue_line(
        "markers", "slow: marca tests que son lentos"
    )
    config.addinivalue_line(
        "markers", "integration: marca tests de integración"
    )
    config.addinivalue_line(
        "markers", "unit: marca tests unitarios"
    )
    config.addinivalue_line(
        "markers", "auth: marca tests de autenticación"
    )
    config.addinivalue_line(
        "markers", "database: marca tests de base de datos"
    )
    config.addinivalue_line(
        "markers", "endpoints: marca tests de endpoints"
    )


@pytest.fixture(scope="function")
def db():
    """Fixture que crea una base de datos SQLite en memoria para testing"""
    # Crear engine de SQLite en memoria
    engine = create_engine("sqlite:///:memory:", echo=False)
    
    # Crear todas las tablas
    Base.metadata.create_all(engine)
    
    # Crear sesión
    SessionLocal = sessionmaker(bind=engine)
    session = SessionLocal()
    
    # Crear datos iniciales necesarios
    _crear_datos_iniciales(session)
    
    yield session
    
    # Cleanup
    session.close()
    engine.dispose()


def _crear_datos_iniciales(session):
    """Crea datos iniciales necesarios para los tests"""
    # Tipos de usuario
    tipo_admin = TipoUsuario(nombre="Administrador", descripcion="Admin")
    tipo_usuario = TipoUsuario(nombre="Usuario", descripcion="Usuario normal")
    session.add_all([tipo_admin, tipo_usuario])
    
    # Estados de usuario
    estado_activo = EstadoUsuario(nombre="Activo", descripcion="Usuario activo")
    estado_inactivo = EstadoUsuario(nombre="Inactivo", descripcion="Usuario inactivo")
    session.add_all([estado_activo, estado_inactivo])
    
    # Tipos de producto
    tipo_producto = TipoProducto(nombre="General", descripcion="Producto general")
    session.add(tipo_producto)
    
    # Estados de producto
    estado_producto = EstadoProducto(nombre="Activo", descripcion="Producto activo")
    session.add(estado_producto)
    
    session.commit()


@pytest.fixture
def usuario(db):
    """Fixture para crear un usuario de prueba"""
    usuario_data = schemas.UsuarioCreate(
        username="testuserf",
        email="test@test.com",
        password="testpass123",
        nombre="Test",
        apellido="User",
        tipo_usuario_id=2,
        estado_usuario_id=1
    )
    usuario = crud_usuario.create(db, obj_in=usuario_data)
    return usuario


@pytest.fixture
def tipo_producto(db):
    """Fixture para obtener tipo de producto"""
    return db.query(TipoProducto).first()


@pytest.fixture
def estado_producto(db):
    """Fixture para obtener estado de producto"""
    return db.query(EstadoProducto).first()


@pytest.fixture(scope="session")
def client():
    """Cliente de prueba para FastAPI"""
    from fastapi.testclient import TestClient
    from app.main import app
    return TestClient(app)


@pytest.fixture(scope="function")
def test_user_token(client, db):
    """Token de autenticación para usuario de prueba"""
    from app.src.auth.password import PasswordHandler
    
    # Crear usuario de prueba si no existe
    usuario = db.query(Usuario).filter(Usuario.username == "testuser").first()
    if not usuario:
        password_handler = PasswordHandler()
        usuario_data = schemas.UsuarioCreate(
            username="testuser",
            email="test@test.com",
            password="testpass123",
            nombre="Test",
            apellido="User",
            tipo_usuario_id=2,
            estado_usuario_id=1
        )
        usuario = crud_usuario.create(db, obj_in=usuario_data)
        db.commit()
    
    # Login para obtener token
    login_data = {"email": "test@test.com", "password": "testpass123"}
    response = client.post("/auth/login", json=login_data)
    assert response.status_code == 200
    token = response.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}
