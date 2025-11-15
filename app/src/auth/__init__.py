"""
Módulo de autenticación para el sistema de inventario
"""

from .jwt import JWTHandler
from .password import PasswordHandler
from .service import AuthService
from .crud import crud_usuario
from .dependencies import (
    get_current_user,
    get_optional_user,
    get_current_admin,
    get_current_active_user,
    require_role,
    auth_service
)
from .schemas import (
    LoginRequest,
    TokenResponse,
    TokenData,
    ChangePasswordRequest,
    ResetPasswordRequest
)

__all__ = [
    "JWTHandler",
    "PasswordHandler",
    "AuthService",
    "crud_usuario",
    "get_current_user",
    "get_optional_user",
    "get_current_admin",
    "get_current_active_user",
    "require_role",
    "auth_service",
    "LoginRequest",
    "TokenResponse",
    "TokenData",
    "ChangePasswordRequest",
    "ResetPasswordRequest"
]
