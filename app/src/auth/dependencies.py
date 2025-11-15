from functools import wraps
from typing import Optional, Callable
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
from app.database.database import get_db
from app.src.auth.service import AuthService
from app.database.models import Usuario
import os

# Configuración global
SECRET_KEY = os.getenv("SECRET_KEY", "change_this_secret_key_in_production")
ALGORITHM = os.getenv("ALGORITHM", "HS256")
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "1440"))

# Instancia global del servicio de autenticación
auth_service = AuthService(
    secret_key=SECRET_KEY,
    algorithm=ALGORITHM,
    access_token_expire_minutes=ACCESS_TOKEN_EXPIRE_MINUTES
)

# Esquema de seguridad
security = HTTPBearer()


def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db)
) -> Usuario:
    """
    Dependencia de FastAPI para obtener el usuario actual del token JWT
    
    Args:
        credentials: Credenciales HTTP Bearer con el token
        db: Sesión de base de datos
        
    Returns:
        Usuario autenticado
        
    Raises:
        HTTPException: Si el token es inválido o el usuario no existe/inactivo
    """
    token = credentials.credentials
    return auth_service.get_current_user(db=db, token=token)


def get_optional_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(HTTPBearer(auto_error=False)),
    db: Session = Depends(get_db)
) -> Optional[Usuario]:
    """
    Dependencia para obtener el usuario si está autenticado, None si no
    Útil para endpoints que funcionan con o sin autenticación
    
    Args:
        credentials: Credenciales HTTP Bearer opcionales
        db: Sesión de base de datos
        
    Returns:
        Usuario autenticado o None
    """
    if not credentials:
        return None
    
    try:
        token = credentials.credentials
        return auth_service.get_current_user(db=db, token=token)
    except HTTPException:
        return None


def require_auth(func: Callable) -> Callable:
    """
    Decorador para requerir autenticación en un endpoint
    
    Uso:
        @app.get("/protected")
        @require_auth
        def protected_endpoint(current_user: Usuario = Depends(get_current_user)):
            return {"user": current_user.username}
    
    Nota: Este decorador es más para claridad visual.
    En FastAPI es mejor usar directamente la dependencia get_current_user
    """
    @wraps(func)
    async def wrapper(*args, **kwargs):
        return await func(*args, **kwargs)
    return wrapper


def require_role(allowed_roles: list[int]):
    """
    Crea un decorador para verificar roles de usuario
    
    Args:
        allowed_roles: Lista de IDs de tipos de usuario permitidos
        
    Uso:
        def get_current_admin(current_user: Usuario = Depends(get_current_user)):
            if current_user.tipo_usuario_id not in [1]:  # Solo admin
                raise HTTPException(status_code=403, detail="No autorizado")
            return current_user
            
        @app.get("/admin")
        def admin_endpoint(admin: Usuario = Depends(get_current_admin)):
            return {"message": "Admin access"}
    """
    def role_checker(current_user: Usuario = Depends(get_current_user)) -> Usuario:
        if current_user.tipo_usuario_id not in allowed_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="No tiene permisos suficientes para acceder a este recurso"
            )
        return current_user
    
    return role_checker


# Dependencias comunes pre-configuradas
def get_current_admin(current_user: Usuario = Depends(get_current_user)) -> Usuario:
    """
    Dependencia para verificar que el usuario es administrador
    Asume que tipo_usuario_id = 1 es admin
    """
    if current_user.tipo_usuario_id != 1:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Se requieren permisos de administrador"
        )
    return current_user


def get_current_active_user(current_user: Usuario = Depends(get_current_user)) -> Usuario:
    """
    Dependencia para verificar que el usuario está activo
    (Ya se verifica en get_current_user, pero aquí por claridad)
    """
    return current_user
