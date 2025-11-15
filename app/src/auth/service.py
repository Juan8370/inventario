from datetime import timedelta
from typing import Optional
from sqlalchemy.orm import Session
from fastapi import HTTPException, status
from app.src.auth.jwt import JWTHandler
from app.src.auth.crud import crud_usuario
from app.src.auth.schemas import LoginRequest, TokenResponse, TokenData
from app.database.models import Usuario


class AuthService:
    """Servicio de autenticación que integra JWT y gestión de usuarios"""
    
    def __init__(self, secret_key: str, algorithm: str = "HS256", access_token_expire_minutes: int = 1440):
        """
        Inicializa el servicio de autenticación
        
        Args:
            secret_key: Clave secreta para firmar los tokens
            algorithm: Algoritmo de encriptación (por defecto HS256)
            access_token_expire_minutes: Minutos de expiración del token (por defecto 24 horas)
        """
        self.jwt_handler = JWTHandler(secret_key=secret_key, algorithm=algorithm)
        self.access_token_expire_minutes = access_token_expire_minutes
    
    def login(self, db: Session, login_data: LoginRequest) -> TokenResponse:
        """
        Autentica un usuario y genera un token JWT
        
        Args:
            db: Sesión de base de datos
            login_data: Datos de login (email y password)
            
        Returns:
            TokenResponse con el token de acceso y datos del usuario
            
        Raises:
            HTTPException: Si las credenciales son incorrectas o el usuario está inactivo
        """
        # Autenticar usuario
        usuario = crud_usuario.authenticate(
            db=db,
            email=login_data.email,
            password=login_data.password
        )
        
        if not usuario:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Email o contraseña incorrectos",
                headers={"WWW-Authenticate": "Bearer"}
            )
        
        # Verificar si el usuario está activo
        if not crud_usuario.is_active(usuario):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Usuario inactivo. Contacte al administrador"
            )
        
        # Actualizar fecha de último acceso
        crud_usuario.update_last_access(db=db, usuario_id=usuario.id)
        
        # Crear token
        token_data = {
            "user_id": usuario.id,
            "username": usuario.username,
            "email": usuario.email,
            "tipo_usuario_id": usuario.tipo_usuario_id
        }
        
        expires_delta = timedelta(minutes=self.access_token_expire_minutes)
        access_token = self.jwt_handler.create_token(
            data=token_data,
            expires_delta=expires_delta
        )
        
        return TokenResponse(
            access_token=access_token,
            token_type="bearer",
            expires_in=self.access_token_expire_minutes * 60,  # Convertir a segundos
            user_id=usuario.id,
            username=usuario.username,
            email=usuario.email
        )
    
    def verify_token(self, token: str) -> Optional[TokenData]:
        """
        Verifica un token JWT y extrae los datos del usuario
        
        Args:
            token: Token JWT a verificar
            
        Returns:
            TokenData con los datos del usuario si el token es válido, None en caso contrario
        """
        payload = self.jwt_handler.verify_token(token)
        
        if payload is None:
            return None
        
        return TokenData(
            user_id=payload.get("user_id"),
            username=payload.get("username"),
            email=payload.get("email"),
            tipo_usuario_id=payload.get("tipo_usuario_id")
        )
    
    def get_current_user(self, db: Session, token: str) -> Usuario:
        """
        Obtiene el usuario actual a partir del token JWT
        
        Args:
            db: Sesión de base de datos
            token: Token JWT
            
        Returns:
            Usuario autenticado
            
        Raises:
            HTTPException: Si el token es inválido o el usuario no existe
        """
        credentials_exception = HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="No se pudieron validar las credenciales",
            headers={"WWW-Authenticate": "Bearer"}
        )
        
        # Verificar token
        token_data = self.verify_token(token)
        
        if token_data is None or token_data.user_id is None:
            raise credentials_exception
        
        # Obtener usuario
        usuario = crud_usuario.get(db=db, id=token_data.user_id)
        
        if usuario is None:
            raise credentials_exception
        
        # Verificar que el usuario esté activo
        if not crud_usuario.is_active(usuario):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Usuario inactivo"
            )
        
        return usuario
    
    def refresh_token(self, db: Session, old_token: str) -> TokenResponse:
        """
        Refresca un token JWT generando uno nuevo
        
        Args:
            db: Sesión de base de datos
            old_token: Token actual
            
        Returns:
            TokenResponse con el nuevo token
            
        Raises:
            HTTPException: Si el token es inválido
        """
        # Obtener usuario del token actual
        usuario = self.get_current_user(db=db, token=old_token)
        
        # Crear nuevo token
        token_data = {
            "user_id": usuario.id,
            "username": usuario.username,
            "email": usuario.email,
            "tipo_usuario_id": usuario.tipo_usuario_id
        }
        
        expires_delta = timedelta(minutes=self.access_token_expire_minutes)
        access_token = self.jwt_handler.create_token(
            data=token_data,
            expires_delta=expires_delta
        )
        
        return TokenResponse(
            access_token=access_token,
            token_type="bearer",
            expires_in=self.access_token_expire_minutes * 60,
            user_id=usuario.id,
            username=usuario.username,
            email=usuario.email
        )
