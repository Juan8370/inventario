from pydantic import BaseModel, EmailStr, Field
from typing import Optional
from datetime import datetime


class LoginRequest(BaseModel):
    """Esquema para la solicitud de login"""
    email: EmailStr = Field(..., description="Email del usuario")
    password: str = Field(..., min_length=1, description="Contraseña del usuario")


class TokenResponse(BaseModel):
    """Esquema para la respuesta de autenticación"""
    access_token: str = Field(..., description="Token JWT de acceso")
    token_type: str = Field(default="bearer", description="Tipo de token")
    expires_in: int = Field(..., description="Tiempo de expiración en segundos")
    user_id: int = Field(..., description="ID del usuario autenticado")
    username: str = Field(..., description="Nombre de usuario")
    email: str = Field(..., description="Email del usuario")


class TokenData(BaseModel):
    """Esquema para los datos contenidos en el token"""
    user_id: Optional[int] = None
    username: Optional[str] = None
    email: Optional[str] = None
    tipo_usuario_id: Optional[int] = None


class ChangePasswordRequest(BaseModel):
    """Esquema para cambiar contraseña"""
    current_password: str = Field(..., min_length=1, description="Contraseña actual")
    new_password: str = Field(..., min_length=8, description="Nueva contraseña")


class ResetPasswordRequest(BaseModel):
    """Esquema para resetear contraseña (sin contraseña actual)"""
    email: EmailStr = Field(..., description="Email del usuario")
    new_password: str = Field(..., min_length=8, description="Nueva contraseña")
