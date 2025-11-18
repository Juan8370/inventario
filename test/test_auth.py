"""
Tests para el sistema de autenticación
"""
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.main import app
from app.src.database.database import get_db
from app.src.database.models import Base, Usuario, TipoUsuario, EstadoUsuario
from app.src.auth import (
    PasswordHandler, 
    JWTHandler, 
    AuthService, 
    crud_usuario,
    LoginRequest
)


# Configurar base de datos de prueba en memoria
TEST_DATABASE_URL = "sqlite:///:memory:"

engine = create_engine(
    TEST_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=__import__('sqlalchemy.pool', fromlist=['StaticPool']).StaticPool
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


# Override de la dependencia get_db para este módulo
def override_get_db_auth():
    try:
        db = TestingSessionLocal()
        yield db
    finally:
        db.close()


# Cliente de prueba
client = TestClient(app)

# Aplicar override solo cuando se usen estos tests
app.dependency_overrides[get_db] = override_get_db_auth


@pytest.fixture(scope="module")
def setup_auth_database():
    """Crear las tablas antes de los tests y eliminarlas después"""
    # Asegurar que el override esté activo
    app.dependency_overrides[get_db] = override_get_db_auth
    
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)
    engine.dispose()
    
    # Limpiar overrides al terminar
    if get_db in app.dependency_overrides:
        del app.dependency_overrides[get_db]


@pytest.fixture(scope="function")
def clean_auth_database():
    """Limpiar datos entre tests"""
    yield  # Ejecutar test primero
    # Limpiar después del test
    db = TestingSessionLocal()
    try:
        for table in reversed(Base.metadata.sorted_tables):
            db.execute(table.delete())
        db.commit()
    finally:
        db.close()


@pytest.fixture
def setup_test_user(clean_auth_database):
    """Crear usuario de prueba"""
    db = TestingSessionLocal()
    try:
        # Crear tipo y estado de usuario
        tipo_usuario = TipoUsuario(nombre="Admin", descripcion="Administrador")
        estado_usuario = EstadoUsuario(nombre="Activo", descripcion="Usuario activo", activo=True)
        db.add_all([tipo_usuario, estado_usuario])
        db.commit()
        db.refresh(tipo_usuario)
        db.refresh(estado_usuario)
        
        # Crear usuario con contraseña hasheada
        from app.src.database.schemas import UsuarioCreate
        usuario_data = UsuarioCreate(
            username="testuser",
            email="test@example.com",
            password="password123",
            nombre="Test",
            apellido="User",
            tipo_usuario_id=tipo_usuario.id,
            estado_usuario_id=estado_usuario.id
        )
        
        usuario = crud_usuario.create(db=db, obj_in=usuario_data)
        
        return {
            "id": usuario.id,
            "username": "testuser",
            "email": "test@example.com",
            "password": "password123",
            "tipo_usuario_id": tipo_usuario.id,
            "estado_usuario_id": estado_usuario.id
        }
    finally:
        db.close()


class TestPasswordHandler:
    """Tests para el manejador de contraseñas"""
    
    def test_hash_password(self):
        """Verificar que se hasheen las contraseñas correctamente"""
        password = "mypassword123"
        hashed = PasswordHandler.hash_password(password)
        
        assert hashed is not None
        assert hashed != password
        assert len(hashed) > 0
        assert hashed.startswith("$2b$")  # bcrypt hash
        print("✅ Hash de contraseña funciona correctamente")
    
    def test_verify_password_correct(self):
        """Verificar que se verifique una contraseña correcta"""
        password = "mypassword123"
        hashed = PasswordHandler.hash_password(password)
        
        is_valid = PasswordHandler.verify_password(password, hashed)
        assert is_valid is True
        print("✅ Verificación de contraseña correcta funciona")
    
    def test_verify_password_incorrect(self):
        """Verificar que se rechace una contraseña incorrecta"""
        password = "mypassword123"
        hashed = PasswordHandler.hash_password(password)
        
        is_valid = PasswordHandler.verify_password("wrongpassword", hashed)
        assert is_valid is False
        print("✅ Verificación de contraseña incorrecta funciona")
    
    def test_hash_same_password_different_hashes(self):
        """Verificar que el mismo password genere hashes diferentes (salt)"""
        password = "mypassword123"
        hash1 = PasswordHandler.hash_password(password)
        hash2 = PasswordHandler.hash_password(password)
        
        assert hash1 != hash2  # Diferentes debido al salt
        assert PasswordHandler.verify_password(password, hash1)
        assert PasswordHandler.verify_password(password, hash2)
        print("✅ Salt en hash de contraseñas funciona correctamente")


class TestJWTHandler:
    """Tests para el manejador de JWT"""
    
    def test_create_token(self):
        """Verificar creación de token JWT"""
        jwt_handler = JWTHandler(secret_key="test_secret_key")
        
        data = {"user_id": 1, "username": "testuser"}
        token = jwt_handler.create_token(data)
        
        assert token is not None
        assert isinstance(token, str)
        assert len(token) > 0
        print("✅ Creación de token JWT funciona correctamente")
    
    def test_verify_token_valid(self):
        """Verificar token JWT válido"""
        jwt_handler = JWTHandler(secret_key="test_secret_key")
        
        data = {"user_id": 1, "username": "testuser"}
        token = jwt_handler.create_token(data)
        
        payload = jwt_handler.verify_token(token)
        
        assert payload is not None
        assert payload["user_id"] == 1
        assert payload["username"] == "testuser"
        assert "exp" in payload
        print("✅ Verificación de token JWT válido funciona")
    
    def test_verify_token_invalid(self):
        """Verificar que se rechace un token inválido"""
        jwt_handler = JWTHandler(secret_key="test_secret_key")
        
        invalid_token = "invalid.token.here"
        payload = jwt_handler.verify_token(invalid_token)
        
        assert payload is None
        print("✅ Rechazo de token inválido funciona")
    
    def test_verify_token_wrong_secret(self):
        """Verificar que un token con secret diferente sea rechazado"""
        jwt_handler1 = JWTHandler(secret_key="secret1")
        jwt_handler2 = JWTHandler(secret_key="secret2")
        
        data = {"user_id": 1}
        token = jwt_handler1.create_token(data)
        
        payload = jwt_handler2.verify_token(token)
        assert payload is None
        print("✅ Rechazo de token con secret diferente funciona")
    
    def test_token_with_expiration(self):
        """Verificar token con tiempo de expiración"""
        from datetime import timedelta
        
        jwt_handler = JWTHandler(secret_key="test_secret_key")
        
        data = {"user_id": 1}
        token = jwt_handler.create_token(data, expires_delta=timedelta(hours=1))
        
        payload = jwt_handler.verify_token(token)
        assert payload is not None
        assert "exp" in payload
        print("✅ Token con expiración funciona correctamente")
    
    def test_decode_without_verification(self):
        """Verificar decodificación sin verificar firma"""
        jwt_handler = JWTHandler(secret_key="test_secret_key")
        
        data = {"user_id": 1, "username": "test"}
        token = jwt_handler.create_token(data)
        
        payload = jwt_handler.decode_token_without_verification(token)
        
        assert payload is not None
        assert payload["user_id"] == 1
        print("✅ Decodificación sin verificación funciona")


class TestCRUDUsuario:
    """Tests para las operaciones CRUD de usuarios"""
    
    def test_create_user_with_hashed_password(self, setup_auth_database, clean_auth_database):
        """Verificar que se cree usuario con contraseña hasheada"""
        db = TestingSessionLocal()
        try:
            # Crear tipo y estado
            tipo = TipoUsuario(nombre="Test")
            estado = EstadoUsuario(nombre="Activo", activo=True)
            db.add_all([tipo, estado])
            db.commit()
            db.refresh(tipo)
            db.refresh(estado)
            
            # Crear usuario
            from app.src.database.schemas import UsuarioCreate
            usuario_data = UsuarioCreate(
                username="newuser",
                email="new@example.com",
                password="plainpassword123",
                nombre="New",
                apellido="User",
                tipo_usuario_id=tipo.id,
                estado_usuario_id=estado.id
            )
            
            usuario = crud_usuario.create(db=db, obj_in=usuario_data)
            
            assert usuario.id is not None
            assert usuario.username == "newuser"
            assert usuario.email == "new@example.com"
            assert usuario.password_hash != "plainpassword123"
            assert usuario.password_hash.startswith("$2b$")
            print("✅ Creación de usuario con password hasheado funciona")
        finally:
            db.close()
    
    def test_get_user_by_email(self, setup_auth_database, setup_test_user):
        """Verificar obtención de usuario por email"""
        db = TestingSessionLocal()
        try:
            usuario = crud_usuario.get_by_email(db=db, email="test@example.com")
            
            assert usuario is not None
            assert usuario.email == "test@example.com"
            assert usuario.username == "testuser"
            print("✅ Obtener usuario por email funciona")
        finally:
            db.close()
    
    def test_get_user_by_username(self, setup_auth_database, setup_test_user):
        """Verificar obtención de usuario por username"""
        db = TestingSessionLocal()
        try:
            usuario = crud_usuario.get_by_username(db=db, username="testuser")
            
            assert usuario is not None
            assert usuario.username == "testuser"
            assert usuario.email == "test@example.com"
            print("✅ Obtener usuario por username funciona")
        finally:
            db.close()
    
    def test_authenticate_user_success(self, setup_auth_database, setup_test_user):
        """Verificar autenticación exitosa de usuario"""
        db = TestingSessionLocal()
        try:
            usuario = crud_usuario.authenticate(
                db=db,
                email="test@example.com",
                password="password123"
            )
            
            assert usuario is not None
            assert usuario.email == "test@example.com"
            print("✅ Autenticación exitosa funciona")
        finally:
            db.close()
    
    def test_authenticate_user_wrong_password(self, setup_auth_database, setup_test_user):
        """Verificar que falle con contraseña incorrecta"""
        db = TestingSessionLocal()
        try:
            usuario = crud_usuario.authenticate(
                db=db,
                email="test@example.com",
                password="wrongpassword"
            )
            
            assert usuario is None
            print("✅ Rechazo de contraseña incorrecta funciona")
        finally:
            db.close()
    
    def test_authenticate_user_wrong_email(self, setup_auth_database, setup_test_user):
        """Verificar que falle con email inexistente"""
        db = TestingSessionLocal()
        try:
            usuario = crud_usuario.authenticate(
                db=db,
                email="nonexistent@example.com",
                password="password123"
            )
            
            assert usuario is None
            print("✅ Rechazo de email inexistente funciona")
        finally:
            db.close()
    
    def test_change_password_success(self, setup_auth_database, setup_test_user):
        """Verificar cambio de contraseña exitoso"""
        db = TestingSessionLocal()
        try:
            success = crud_usuario.change_password(
                db=db,
                usuario_id=setup_test_user["id"],
                current_password="password123",
                new_password="newpassword456"
            )
            
            assert success is True
            
            # Verificar que pueda autenticarse con la nueva contraseña
            usuario = crud_usuario.authenticate(
                db=db,
                email="test@example.com",
                password="newpassword456"
            )
            assert usuario is not None
            
            # Verificar que no pueda con la vieja
            usuario = crud_usuario.authenticate(
                db=db,
                email="test@example.com",
                password="password123"
            )
            assert usuario is None
            print("✅ Cambio de contraseña funciona correctamente")
        finally:
            db.close()
    
    def test_change_password_wrong_current(self, setup_auth_database, setup_test_user):
        """Verificar que falle con contraseña actual incorrecta"""
        db = TestingSessionLocal()
        try:
            success = crud_usuario.change_password(
                db=db,
                usuario_id=setup_test_user["id"],
                current_password="wrongcurrent",
                new_password="newpassword456"
            )
            
            assert success is False
            print("✅ Rechazo de cambio con contraseña actual incorrecta funciona")
        finally:
            db.close()
    
    def test_reset_password(self, setup_auth_database, setup_test_user):
        """Verificar reset de contraseña"""
        db = TestingSessionLocal()
        try:
            success = crud_usuario.reset_password(
                db=db,
                email="test@example.com",
                new_password="resetpassword789"
            )
            
            assert success is True
            
            # Verificar que pueda autenticarse con la nueva contraseña
            usuario = crud_usuario.authenticate(
                db=db,
                email="test@example.com",
                password="resetpassword789"
            )
            assert usuario is not None
            print("✅ Reset de contraseña funciona correctamente")
        finally:
            db.close()


class TestAuthService:
    """Tests para el servicio de autenticación"""
    
    def test_login_success(self, setup_auth_database, setup_test_user):
        """Verificar login exitoso"""
        db = TestingSessionLocal()
        try:
            auth_service = AuthService(secret_key="test_secret")
            
            login_data = LoginRequest(
                email="test@example.com",
                password="password123"
            )
            
            response = auth_service.login(db=db, login_data=login_data)
            
            assert response.access_token is not None
            assert response.token_type == "bearer"
            assert response.user_id == setup_test_user["id"]
            assert response.username == "testuser"
            assert response.email == "test@example.com"
            assert response.expires_in > 0
            print("✅ Login exitoso funciona correctamente")
        finally:
            db.close()
    
    def test_login_wrong_password(self, setup_auth_database, setup_test_user):
        """Verificar que falle login con contraseña incorrecta"""
        db = TestingSessionLocal()
        try:
            auth_service = AuthService(secret_key="test_secret")
            
            login_data = LoginRequest(
                email="test@example.com",
                password="wrongpassword"
            )
            
            from fastapi import HTTPException
            with pytest.raises(HTTPException) as exc_info:
                auth_service.login(db=db, login_data=login_data)
            
            assert exc_info.value.status_code == 401
            print("✅ Rechazo de login con contraseña incorrecta funciona")
        finally:
            db.close()
    
    def test_login_inactive_user(self, setup_auth_database, clean_auth_database):
        """Verificar que falle login con usuario inactivo"""
        db = TestingSessionLocal()
        try:
            # Crear usuario inactivo
            tipo = TipoUsuario(nombre="Test")
            estado = EstadoUsuario(nombre="Inactivo", activo=False)
            db.add_all([tipo, estado])
            db.commit()
            db.refresh(tipo)
            db.refresh(estado)
            
            from app.src.database.schemas import UsuarioCreate
            usuario_data = UsuarioCreate(
                username="inactive",
                email="inactive@example.com",
                password="password123",
                nombre="Inactive",
                apellido="User",
                tipo_usuario_id=tipo.id,
                estado_usuario_id=estado.id
            )
            crud_usuario.create(db=db, obj_in=usuario_data)
            
            # Intentar login
            auth_service = AuthService(secret_key="test_secret")
            login_data = LoginRequest(
                email="inactive@example.com",
                password="password123"
            )
            
            from fastapi import HTTPException
            with pytest.raises(HTTPException) as exc_info:
                auth_service.login(db=db, login_data=login_data)
            
            assert exc_info.value.status_code == 403
            print("✅ Rechazo de usuario inactivo funciona")
        finally:
            db.close()
    
    def test_verify_token_valid(self, setup_auth_database, setup_test_user):
        """Verificar validación de token"""
        db = TestingSessionLocal()
        try:
            auth_service = AuthService(secret_key="test_secret")
            
            # Hacer login primero
            login_data = LoginRequest(
                email="test@example.com",
                password="password123"
            )
            response = auth_service.login(db=db, login_data=login_data)
            
            # Verificar token
            token_data = auth_service.verify_token(response.access_token)
            
            assert token_data is not None
            assert token_data.user_id == setup_test_user["id"]
            assert token_data.username == "testuser"
            assert token_data.email == "test@example.com"
            print("✅ Verificación de token funciona correctamente")
        finally:
            db.close()
    
    def test_get_current_user(self, setup_auth_database, setup_test_user):
        """Verificar obtención de usuario actual desde token"""
        db = TestingSessionLocal()
        try:
            auth_service = AuthService(secret_key="test_secret")
            
            # Login
            login_data = LoginRequest(
                email="test@example.com",
                password="password123"
            )
            response = auth_service.login(db=db, login_data=login_data)
            
            # Obtener usuario actual
            usuario = auth_service.get_current_user(db=db, token=response.access_token)
            
            assert usuario is not None
            assert usuario.id == setup_test_user["id"]
            assert usuario.username == "testuser"
            assert usuario.email == "test@example.com"
            print("✅ Obtener usuario actual desde token funciona")
        finally:
            db.close()


class TestAuthEndpoints:
    """Tests para los endpoints de autenticación"""
    
    def test_login_endpoint_success(self, setup_auth_database, setup_test_user):
        """Verificar endpoint de login exitoso"""
        response = client.post(
            "/auth/login",
            json={
                "email": "test@example.com",
                "password": "password123"
            }
        )
        
        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert data["token_type"] == "bearer"
        assert data["user_id"] == setup_test_user["id"]
        assert data["username"] == "testuser"
        print("✅ Endpoint de login funciona correctamente")
    
    def test_login_endpoint_wrong_credentials(self, setup_auth_database, setup_test_user):
        """Verificar endpoint de login con credenciales incorrectas"""
        response = client.post(
            "/auth/login",
            json={
                "email": "test@example.com",
                "password": "wrongpassword"
            }
        )
        
        assert response.status_code == 401
        print("✅ Rechazo en endpoint de login funciona")
    
    def test_get_profile_endpoint_authenticated(self, setup_auth_database, setup_test_user):
        """Verificar endpoint de perfil con autenticación"""
        # Primero hacer login
        login_response = client.post(
            "/auth/login",
            json={
                "email": "test@example.com",
                "password": "password123"
            }
        )
        token = login_response.json()["access_token"]
        
        # Obtener perfil
        response = client.get(
            "/auth/me",
            headers={"Authorization": f"Bearer {token}"}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["username"] == "testuser"
        assert data["email"] == "test@example.com"
        print("✅ Endpoint de perfil con autenticación funciona")
    
    def test_get_profile_endpoint_unauthenticated(self, setup_auth_database):
        """Verificar que el endpoint de perfil requiera autenticación"""
        response = client.get("/auth/me")
        
        assert response.status_code == 403  # Forbidden sin token
        print("✅ Endpoint de perfil rechaza acceso sin autenticación")
    
    def test_get_profile_endpoint_invalid_token(self, setup_auth_database):
        """Verificar endpoint de perfil con token inválido"""
        response = client.get(
            "/auth/me",
            headers={"Authorization": "Bearer invalid_token_here"}
        )
        
        assert response.status_code == 401
        print("✅ Endpoint de perfil rechaza token inválido")
    
    def test_change_password_endpoint(self, setup_auth_database, setup_test_user):
        """Verificar endpoint de cambio de contraseña"""
        # Login
        login_response = client.post(
            "/auth/login",
            json={
                "email": "test@example.com",
                "password": "password123"
            }
        )
        token = login_response.json()["access_token"]
        
        # Cambiar contraseña
        response = client.post(
            "/auth/change-password",
            headers={"Authorization": f"Bearer {token}"},
            json={
                "current_password": "password123",
                "new_password": "newpassword456"
            }
        )
        
        assert response.status_code == 200
        assert "exitosamente" in response.json()["message"]
        
        # Verificar que pueda hacer login con la nueva contraseña
        new_login_response = client.post(
            "/auth/login",
            json={
                "email": "test@example.com",
                "password": "newpassword456"
            }
        )
        assert new_login_response.status_code == 200
        print("✅ Endpoint de cambio de contraseña funciona")


class TestProtectedEndpoints:
    """Tests para endpoints protegidos"""
    
    def test_protected_endpoint_with_auth(self, setup_auth_database, setup_test_user):
        """Verificar acceso a endpoint protegido con autenticación"""
        # Login
        login_response = client.post(
            "/auth/login",
            json={
                "email": "test@example.com",
                "password": "password123"
            }
        )
        token = login_response.json()["access_token"]
        
        # Acceder a endpoint protegido (stats)
        response = client.get(
            "/stats",
            headers={"Authorization": f"Bearer {token}"}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert "total_productos" in data
        assert "usuario_actual" in data
        print("✅ Acceso a endpoint protegido con auth funciona")
    
    def test_protected_endpoint_without_auth(self, setup_auth_database):
        """Verificar rechazo de endpoint protegido sin autenticación"""
        response = client.get("/stats")
        
        assert response.status_code == 403
        print("✅ Rechazo de endpoint protegido sin auth funciona")
    
    def test_optional_auth_endpoint_without_token(self, setup_auth_database):
        """Verificar endpoint con auth opcional sin token"""
        response = client.get("/productos")
        
        assert response.status_code == 200
        print("✅ Endpoint con auth opcional funciona sin token")
    
    def test_optional_auth_endpoint_with_token(self, setup_auth_database, setup_test_user):
        """Verificar endpoint con auth opcional con token"""
        # Login
        login_response = client.post(
            "/auth/login",
            json={
                "email": "test@example.com",
                "password": "password123"
            }
        )
        token = login_response.json()["access_token"]
        
        # Acceder con token
        response = client.get(
            "/productos",
            headers={"Authorization": f"Bearer {token}"}
        )
        
        assert response.status_code == 200
        print("✅ Endpoint con auth opcional funciona con token")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
