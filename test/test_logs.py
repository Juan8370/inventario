"""
Tests para el sistema de Logs
Los logs deben ser INMUTABLES y seguir las reglas de visibilidad
"""
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from datetime import datetime

from app.main import app
from app.src.database.database import get_db
from app.src.database.models import Base, Usuario, TipoUsuario, EstadoUsuario, TipoLog, Log
from app.src.database.schemas import LogCreate, UsuarioCreate
from app.src.database.crud import crud_log, crud_tipo_log
from app.src.database.log_helper import (
    log_error, log_warning, log_info, log_login, log_signup
)
from app.src.auth import crud_usuario
from app.src.auth.password import PasswordHandler

# Configurar base de datos de prueba en memoria
TEST_DATABASE_URL = "sqlite:///:memory:"

engine = create_engine(
    TEST_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=__import__('sqlalchemy.pool', fromlist=['StaticPool']).StaticPool
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def override_get_db_logs():
    try:
        db = TestingSessionLocal()
        yield db
    finally:
        db.close()


client = TestClient(app)
app.dependency_overrides[get_db] = override_get_db_logs


@pytest.fixture(scope="module")
def setup_logs_database():
    """Crear las tablas antes de los tests"""
    app.dependency_overrides[get_db] = override_get_db_logs
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)
    engine.dispose()
    
    if get_db in app.dependency_overrides:
        del app.dependency_overrides[get_db]


@pytest.fixture(scope="function")
def clean_logs_database():
    """Limpiar datos entre tests"""
    yield
    db = TestingSessionLocal()
    try:
        for table in reversed(Base.metadata.sorted_tables):
            db.execute(table.delete())
        db.commit()
    finally:
        db.close()


@pytest.fixture
def setup_tipos_log(clean_logs_database):
    """Crear tipos de log por defecto"""
    db = TestingSessionLocal()
    try:
        tipos = [
            {"nombre": "ERROR", "descripcion": "Errores críticos"},
            {"nombre": "WARNING", "descripcion": "Advertencias"},
            {"nombre": "INFO", "descripcion": "Información"},
            {"nombre": "LOGIN", "descripcion": "Inicios de sesión"},
            {"nombre": "SIGNUP", "descripcion": "Registros de usuario"},
        ]
        
        tipo_ids = {}
        for tipo_data in tipos:
            tipo = TipoLog(**tipo_data)
            db.add(tipo)
            db.flush()
            tipo_ids[tipo_data["nombre"]] = tipo.id
        
        db.commit()
        return tipo_ids
    finally:
        db.close()


@pytest.fixture
def setup_test_users_for_logs(setup_tipos_log):
    """Crear usuarios de prueba para logs"""
    db = TestingSessionLocal()
    try:
        password_handler = PasswordHandler()
        
        # Crear tipos y estados
        tipo_admin = TipoUsuario(nombre="Administrador", descripcion="Admin")
        tipo_user = TipoUsuario(nombre="Usuario", descripcion="User")
        estado_activo = EstadoUsuario(nombre="Activo", descripcion="Activo", activo=True)
        
        db.add_all([tipo_admin, tipo_user, estado_activo])
        db.flush()
        
        # Crear usuarios
        admin = Usuario(
            username="admin_logs",
            email="admin_logs@test.com",
            password_hash=password_handler.hash_password("admin123"),
            nombre="Admin",
            apellido="Logs",
            tipo_usuario_id=tipo_admin.id,
            estado_usuario_id=estado_activo.id
        )
        
        user = Usuario(
            username="user_logs",
            email="user_logs@test.com",
            password_hash=password_handler.hash_password("user123"),
            nombre="User",
            apellido="Logs",
            tipo_usuario_id=tipo_user.id,
            estado_usuario_id=estado_activo.id
        )
        
        db.add_all([admin, user])
        db.commit()
        db.refresh(admin)
        db.refresh(user)
        
        return {
            "admin": {"id": admin.id, "username": "admin_logs", "password": "admin123"},
            "user": {"id": user.id, "username": "user_logs", "password": "user123"}
        }
    finally:
        db.close()


class TestTipoLog:
    """Tests para tipos de log"""
    
    def test_crear_tipos_log(self, setup_logs_database, clean_logs_database):
        """Verificar que se pueden crear tipos de log"""
        db = TestingSessionLocal()
        try:
            tipo = TipoLog(nombre="TEST", descripcion="Tipo de prueba")
            db.add(tipo)
            db.commit()
            db.refresh(tipo)
            
            assert tipo.id is not None
            assert tipo.nombre == "TEST"
            assert tipo.activo is True
        finally:
            db.close()
    
    def test_tipos_log_por_defecto(self, setup_tipos_log):
        """Verificar que existen los tipos de log esperados"""
        db = TestingSessionLocal()
        try:
            tipos = crud_tipo_log.get_multi(db, limit=10)
            nombres = [t.nombre for t in tipos]
            
            assert "ERROR" in nombres
            assert "WARNING" in nombres
            assert "INFO" in nombres
            assert "LOGIN" in nombres
            assert "SIGNUP" in nombres
        finally:
            db.close()


class TestLogCRUD:
    """Tests para operaciones CRUD de logs"""
    
    def test_crear_log_system(self, setup_tipos_log):
        """Verificar que se puede crear un log de SYSTEM"""
        db = TestingSessionLocal()
        try:
            tipo_ids = setup_tipos_log
            
            log_data = LogCreate(
                descripcion="Log de prueba del sistema",
                usuario_tipo="SYSTEM",
                tipo_log_id=tipo_ids["INFO"],
                usuario_id=None
            )
            
            log = crud_log.create(db=db, obj_in=log_data)
            
            assert log.id is not None
            assert log.descripcion == "Log de prueba del sistema"
            assert log.usuario_tipo == "SYSTEM"
            assert log.usuario_id is None
            assert log.fecha is not None
        finally:
            db.close()
    
    def test_crear_log_usuario(self, setup_test_users_for_logs):
        """Verificar que se puede crear un log de USUARIO"""
        db = TestingSessionLocal()
        try:
            users = setup_test_users_for_logs
            tipo_info = crud_tipo_log.get_by_field(db, "nombre", "INFO")
            
            log_data = LogCreate(
                descripcion="Acción del usuario",
                usuario_tipo="USUARIO",
                tipo_log_id=tipo_info.id,
                usuario_id=users["user"]["id"]
            )
            
            log = crud_log.create(db=db, obj_in=log_data)
            
            assert log.id is not None
            assert log.usuario_tipo == "USUARIO"
            assert log.usuario_id == users["user"]["id"]
        finally:
            db.close()
    
    def test_validacion_system_sin_usuario(self, setup_tipos_log):
        """Verificar que logs SYSTEM no deben tener usuario_id"""
        db = TestingSessionLocal()
        try:
            tipo_ids = setup_tipos_log
            users_setup = setup_test_users_for_logs
            
            # Intentar crear log SYSTEM con usuario_id debe fallar en validación
            with pytest.raises(ValueError, match="Los logs de tipo SYSTEM no deben tener usuario_id"):
                log_data = LogCreate(
                    descripcion="Log inválido",
                    usuario_tipo="SYSTEM",
                    tipo_log_id=tipo_ids["INFO"],
                    usuario_id=1  # No debería tener usuario_id
                )
        finally:
            db.close()
    
    def test_validacion_usuario_con_usuario_id(self, setup_tipos_log):
        """Verificar que logs USUARIO deben tener usuario_id"""
        db = TestingSessionLocal()
        try:
            tipo_ids = setup_tipos_log
            
            # Intentar crear log USUARIO sin usuario_id debe fallar
            with pytest.raises(ValueError, match="Los logs de tipo USUARIO deben tener usuario_id"):
                log_data = LogCreate(
                    descripcion="Log inválido",
                    usuario_tipo="USUARIO",
                    tipo_log_id=tipo_ids["INFO"],
                    usuario_id=None  # Debería tener usuario_id
                )
        finally:
            db.close()
    
    def test_logs_son_inmutables_update(self, setup_test_users_for_logs):
        """Verificar que los logs NO se pueden actualizar"""
        db = TestingSessionLocal()
        try:
            users = setup_test_users_for_logs
            tipo_info = crud_tipo_log.get_by_field(db, "nombre", "INFO")
            
            # Crear log
            log_data = LogCreate(
                descripcion="Log original",
                usuario_tipo="USUARIO",
                tipo_log_id=tipo_info.id,
                usuario_id=users["user"]["id"]
            )
            log = crud_log.create(db=db, obj_in=log_data)
            
            # Intentar actualizar debe fallar
            from fastapi import HTTPException
            with pytest.raises(HTTPException) as exc_info:
                crud_log.update(db=db, db_obj=log, obj_in={"descripcion": "Modificado"})
            
            assert exc_info.value.status_code == 403
            assert "inmutable" in exc_info.value.detail.lower()
        finally:
            db.close()
    
    def test_logs_son_inmutables_delete(self, setup_test_users_for_logs):
        """Verificar que los logs NO se pueden eliminar"""
        db = TestingSessionLocal()
        try:
            users = setup_test_users_for_logs
            tipo_info = crud_tipo_log.get_by_field(db, "nombre", "INFO")
            
            # Crear log
            log_data = LogCreate(
                descripcion="Log a eliminar",
                usuario_tipo="USUARIO",
                tipo_log_id=tipo_info.id,
                usuario_id=users["user"]["id"]
            )
            log = crud_log.create(db=db, obj_in=log_data)
            
            # Intentar eliminar debe fallar
            from fastapi import HTTPException
            with pytest.raises(HTTPException) as exc_info:
                crud_log.delete(db=db, id=log.id)
            
            assert exc_info.value.status_code == 403
            assert "inmutable" in exc_info.value.detail.lower()
        finally:
            db.close()
    
    def test_obtener_logs_por_usuario(self, setup_test_users_for_logs):
        """Verificar que se pueden obtener logs por usuario"""
        db = TestingSessionLocal()
        try:
            users = setup_test_users_for_logs
            tipo_info = crud_tipo_log.get_by_field(db, "nombre", "INFO")
            
            # Crear varios logs para el usuario
            for i in range(3):
                log_data = LogCreate(
                    descripcion=f"Log {i} del usuario",
                    usuario_tipo="USUARIO",
                    tipo_log_id=tipo_info.id,
                    usuario_id=users["user"]["id"]
                )
                crud_log.create(db=db, obj_in=log_data)
            
            # Obtener logs del usuario
            logs = crud_log.get_by_usuario(db, usuario_id=users["user"]["id"])
            
            assert len(logs) == 3
            assert all(log.usuario_id == users["user"]["id"] for log in logs)
        finally:
            db.close()
    
    def test_obtener_logs_system(self, setup_tipos_log):
        """Verificar que se pueden obtener logs del sistema"""
        db = TestingSessionLocal()
        try:
            tipo_ids = setup_tipos_log
            
            # Crear logs de sistema
            for i in range(2):
                log_data = LogCreate(
                    descripcion=f"Log del sistema {i}",
                    usuario_tipo="SYSTEM",
                    tipo_log_id=tipo_ids["INFO"],
                    usuario_id=None
                )
                crud_log.create(db=db, obj_in=log_data)
            
            # Obtener logs del sistema
            logs = crud_log.get_system_logs(db)
            
            assert len(logs) == 2
            assert all(log.usuario_tipo == "SYSTEM" for log in logs)
        finally:
            db.close()
    
    def test_filtrar_logs_por_tipo(self, setup_test_users_for_logs):
        """Verificar que se pueden filtrar logs por tipo"""
        db = TestingSessionLocal()
        try:
            users = setup_test_users_for_logs
            tipo_error = crud_tipo_log.get_by_field(db, "nombre", "ERROR")
            tipo_info = crud_tipo_log.get_by_field(db, "nombre", "INFO")
            
            # Crear logs de diferentes tipos
            for _ in range(2):
                crud_log.create(db=db, obj_in=LogCreate(
                    descripcion="Error",
                    usuario_tipo="USUARIO",
                    tipo_log_id=tipo_error.id,
                    usuario_id=users["user"]["id"]
                ))
            
            for _ in range(3):
                crud_log.create(db=db, obj_in=LogCreate(
                    descripcion="Info",
                    usuario_tipo="USUARIO",
                    tipo_log_id=tipo_info.id,
                    usuario_id=users["user"]["id"]
                ))
            
            # Filtrar por tipo ERROR
            logs_error = crud_log.get_by_tipo(db, tipo_log_id=tipo_error.id)
            assert len(logs_error) == 2
            
            # Filtrar por tipo INFO
            logs_info = crud_log.get_by_tipo(db, tipo_log_id=tipo_info.id)
            assert len(logs_info) == 3
        finally:
            db.close()


class TestLogHelpers:
    """Tests para funciones helper de logs"""
    
    def test_log_error_helper(self, setup_tipos_log):
        """Verificar helper log_error"""
        db = TestingSessionLocal()
        try:
            log = log_error(db, "Error crítico del sistema")
            
            assert log is not None
            assert log.descripcion == "Error crítico del sistema"
            assert log.usuario_tipo == "SYSTEM"
            assert log.tipo_log.nombre == "ERROR"
        finally:
            db.close()
    
    def test_log_warning_helper(self, setup_tipos_log):
        """Verificar helper log_warning"""
        db = TestingSessionLocal()
        try:
            log = log_warning(db, "Advertencia del sistema")
            
            assert log is not None
            assert log.descripcion == "Advertencia del sistema"
            assert log.tipo_log.nombre == "WARNING"
        finally:
            db.close()
    
    def test_log_info_helper(self, setup_tipos_log):
        """Verificar helper log_info"""
        db = TestingSessionLocal()
        try:
            log = log_info(db, "Información del sistema")
            
            assert log is not None
            assert log.tipo_log.nombre == "INFO"
        finally:
            db.close()
    
    def test_log_login_helper(self, setup_test_users_for_logs):
        """Verificar helper log_login"""
        db = TestingSessionLocal()
        try:
            users = setup_test_users_for_logs
            log = log_login(db, users["user"]["id"], "Usuario inició sesión exitosamente")
            
            assert log is not None
            assert log.usuario_id == users["user"]["id"]
            assert log.usuario_tipo == "USUARIO"
            assert log.tipo_log.nombre == "LOGIN"
        finally:
            db.close()
    
    def test_log_signup_helper(self, setup_test_users_for_logs):
        """Verificar helper log_signup"""
        db = TestingSessionLocal()
        try:
            users = setup_test_users_for_logs
            log = log_signup(db, users["user"]["id"], "Nuevo usuario registrado")
            
            assert log is not None
            assert log.usuario_id == users["user"]["id"]
            assert log.tipo_log.nombre == "SIGNUP"
        finally:
            db.close()
    
    def test_log_con_usuario(self, setup_test_users_for_logs):
        """Verificar que se puede crear log con usuario específico"""
        db = TestingSessionLocal()
        try:
            users = setup_test_users_for_logs
            log = log_info(
                db, 
                "Acción del usuario",
                usuario_id=users["user"]["id"],
                usuario_tipo="USUARIO"
            )
            
            assert log.usuario_id == users["user"]["id"]
            assert log.usuario_tipo == "USUARIO"
        finally:
            db.close()


class TestLogEndpoints:
    """Tests para endpoints de logs"""
    
    def test_crear_log_endpoint_admin(self, setup_test_users_for_logs):
        """Verificar que admin puede crear logs manualmente"""
        users = setup_test_users_for_logs
        
        # Login como admin
        login_response = client.post("/auth/login", json={
            "email": "admin_logs@test.com",
            "password": users["admin"]["password"]
        })
        assert login_response.status_code == 200
        token = login_response.json()["access_token"]
        
        # Obtener tipo de log
        tipos_response = client.get("/logs/tipos", headers={"Authorization": f"Bearer {token}"})
        tipo_info_id = next(t["id"] for t in tipos_response.json() if t["nombre"] == "INFO")
        
        # Crear log
        response = client.post(
            "/logs/",
            json={
                "descripcion": "Log creado por admin",
                "usuario_tipo": "SYSTEM",
                "tipo_log_id": tipo_info_id,
                "usuario_id": None
            },
            headers={"Authorization": f"Bearer {token}"}
        )
        
        assert response.status_code == 201
        data = response.json()
        assert data["descripcion"] == "Log creado por admin"
        assert data["usuario_tipo"] == "SYSTEM"
    
    def test_crear_log_endpoint_usuario_denegado(self, setup_test_users_for_logs):
        """Verificar que usuario normal NO puede crear logs manualmente"""
        users = setup_test_users_for_logs
        
        # Login como usuario
        login_response = client.post("/auth/login", json={
            "email": "user_logs@test.com",
            "password": users["user"]["password"]
        })
        assert login_response.status_code == 200
        token = login_response.json()["access_token"]
        
        # Intentar crear log
        response = client.post(
            "/logs/",
            json={
                "descripcion": "Log no autorizado",
                "usuario_tipo": "SYSTEM",
                "tipo_log_id": 1,
                "usuario_id": None
            },
            headers={"Authorization": f"Bearer {token}"}
        )
        
        assert response.status_code == 403
    
    def test_listar_logs_usuario_ve_solo_propios(self, setup_test_users_for_logs):
        """Verificar que usuarios normales solo ven sus propios logs"""
        db = TestingSessionLocal()
        users = setup_test_users_for_logs
        
        # Crear logs para diferentes usuarios
        tipo_info = crud_tipo_log.get_by_field(db, "nombre", "INFO")
        
        # Logs del usuario
        for i in range(3):
            crud_log.create(db=db, obj_in=LogCreate(
                descripcion=f"Log usuario {i}",
                usuario_tipo="USUARIO",
                tipo_log_id=tipo_info.id,
                usuario_id=users["user"]["id"]
            ))
        
        # Logs del admin
        for i in range(2):
            crud_log.create(db=db, obj_in=LogCreate(
                descripcion=f"Log admin {i}",
                usuario_tipo="USUARIO",
                tipo_log_id=tipo_info.id,
                usuario_id=users["admin"]["id"]
            ))
        
        db.close()
        
        # Login como usuario
        login_response = client.post("/auth/login", json={
            "email": "user_logs@test.com",
            "password": users["user"]["password"]
        })
        assert login_response.status_code == 200
        token = login_response.json()["access_token"]
        
        # Listar logs
        response = client.get("/logs/", headers={"Authorization": f"Bearer {token}"})
        
        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 4  # 3 logs creados + 1 log de LOGIN automático
        assert all(log["usuario_id"] == users["user"]["id"] for log in data["items"])
    
    def test_listar_logs_admin_ve_todos_usuario(self, setup_test_users_for_logs):
        """Verificar que admin ve logs de todos los usuarios"""
        db = TestingSessionLocal()
        users = setup_test_users_for_logs
        
        tipo_info = crud_tipo_log.get_by_field(db, "nombre", "INFO")
        
        # Crear logs de diferentes usuarios
        for i in range(2):
            crud_log.create(db=db, obj_in=LogCreate(
                descripcion=f"Log usuario {i}",
                usuario_tipo="USUARIO",
                tipo_log_id=tipo_info.id,
                usuario_id=users["user"]["id"]
            ))
            crud_log.create(db=db, obj_in=LogCreate(
                descripcion=f"Log admin {i}",
                usuario_tipo="USUARIO",
                tipo_log_id=tipo_info.id,
                usuario_id=users["admin"]["id"]
            ))
        
        db.close()
        
        # Login como admin
        login_response = client.post("/auth/login", json={
            "email": "admin_logs@test.com",
            "password": users["admin"]["password"]
        })
        assert login_response.status_code == 200
        token = login_response.json()["access_token"]
        
        # Listar logs
        response = client.get("/logs/", headers={"Authorization": f"Bearer {token}"})
        
        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 5  # 4 logs creados + 1 log de LOGIN del admin
    
    def test_listar_logs_system_solo_admin(self, setup_test_users_for_logs):
        """Verificar que solo admin puede ver logs del sistema"""
        db = TestingSessionLocal()
        users = setup_test_users_for_logs
        
        tipo_info = crud_tipo_log.get_by_field(db, "nombre", "INFO")
        
        # Crear logs del sistema
        for i in range(3):
            crud_log.create(db=db, obj_in=LogCreate(
                descripcion=f"Log sistema {i}",
                usuario_tipo="SYSTEM",
                tipo_log_id=tipo_info.id,
                usuario_id=None
            ))
        
        db.close()
        
        # Intentar como usuario normal
        login_response = client.post("/auth/login", json={
            "email": "user_logs@test.com",
            "password": users["user"]["password"]
        })
        assert login_response.status_code == 200
        token_user = login_response.json()["access_token"]
        
        response = client.get("/logs/system", headers={"Authorization": f"Bearer {token_user}"})
        assert response.status_code == 403
        
        # Como admin debe funcionar
        login_response = client.post("/auth/login", json={
            "email": "admin_logs@test.com",
            "password": users["admin"]["password"]
        })
        assert login_response.status_code == 200
        token_admin = login_response.json()["access_token"]
        
        response = client.get("/logs/system", headers={"Authorization": f"Bearer {token_admin}"})
        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 3
        assert all(log["usuario_tipo"] == "SYSTEM" for log in data["items"])
    
    def test_endpoint_mis_logs(self, setup_test_users_for_logs):
        """Verificar endpoint /logs/me"""
        db = TestingSessionLocal()
        users = setup_test_users_for_logs
        
        tipo_info = crud_tipo_log.get_by_field(db, "nombre", "INFO")
        
        # Crear logs del usuario
        for i in range(5):
            crud_log.create(db=db, obj_in=LogCreate(
                descripcion=f"Mi log {i}",
                usuario_tipo="USUARIO",
                tipo_log_id=tipo_info.id,
                usuario_id=users["user"]["id"]
            ))
        
        db.close()
        
        # Login
        login_response = client.post("/auth/login", json={
            "email": "user_logs@test.com",
            "password": users["user"]["password"]
        })
        assert login_response.status_code == 200
        token = login_response.json()["access_token"]
        
        # Obtener mis logs
        response = client.get("/logs/me", headers={"Authorization": f"Bearer {token}"})
        
        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 6  # 5 logs creados + 1 log de LOGIN automático
        assert all(log["usuario_id"] == users["user"]["id"] for log in data["items"])
    
    def test_obtener_log_por_id_usuario(self, setup_test_users_for_logs):
        """Verificar que usuario puede ver su propio log por ID"""
        db = TestingSessionLocal()
        users = setup_test_users_for_logs
        
        tipo_info = crud_tipo_log.get_by_field(db, "nombre", "INFO")
        
        # Crear log
        log = crud_log.create(db=db, obj_in=LogCreate(
            descripcion="Log específico",
            usuario_tipo="USUARIO",
            tipo_log_id=tipo_info.id,
            usuario_id=users["user"]["id"]
        ))
        log_id = log.id
        db.close()
        
        # Login
        login_response = client.post("/auth/login", json={
            "email": "user_logs@test.com",
            "password": users["user"]["password"]
        })
        assert login_response.status_code == 200
        token = login_response.json()["access_token"]
        
        # Obtener log
        response = client.get(f"/logs/{log_id}", headers={"Authorization": f"Bearer {token}"})
        
        assert response.status_code == 200
        assert response.json()["id"] == log_id
    
    def test_usuario_no_puede_ver_log_de_otro(self, setup_test_users_for_logs):
        """Verificar que usuario NO puede ver logs de otros usuarios"""
        db = TestingSessionLocal()
        users = setup_test_users_for_logs
        
        tipo_info = crud_tipo_log.get_by_field(db, "nombre", "INFO")
        
        # Crear log del admin
        log = crud_log.create(db=db, obj_in=LogCreate(
            descripcion="Log del admin",
            usuario_tipo="USUARIO",
            tipo_log_id=tipo_info.id,
            usuario_id=users["admin"]["id"]
        ))
        log_id = log.id
        db.close()
        
        # Login como usuario normal
        login_response = client.post("/auth/login", json={
            "email": "user_logs@test.com",
            "password": users["user"]["password"]
        })
        assert login_response.status_code == 200
        token = login_response.json()["access_token"]
        
        # Intentar ver log del admin
        response = client.get(f"/logs/{log_id}", headers={"Authorization": f"Bearer {token}"})
        
        assert response.status_code == 403
    
    def test_listar_tipos_log(self, setup_test_users_for_logs):
        """Verificar endpoint para listar tipos de log"""
        users = setup_test_users_for_logs
        
        # Login
        login_response = client.post("/auth/login", json={
            "email": "user_logs@test.com",
            "password": users["user"]["password"]
        })
        assert login_response.status_code == 200
        token = login_response.json()["access_token"]
        
        # Obtener tipos
        response = client.get("/logs/tipos", headers={"Authorization": f"Bearer {token}"})
        
        assert response.status_code == 200
        tipos = response.json()
        nombres = [t["nombre"] for t in tipos]
        
        assert "ERROR" in nombres
        assert "WARNING" in nombres
        assert "INFO" in nombres
        assert "LOGIN" in nombres
        assert "SIGNUP" in nombres
