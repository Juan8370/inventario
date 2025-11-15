import jwt
from datetime import datetime, timedelta
from typing import Optional, Dict, Any


class JWTHandler:
    """Clase para manejar la creación y verificación de tokens JWT"""
    
    def __init__(self, secret_key: str, algorithm: str = "HS256"):
        """
        Inicializa el manejador de JWT
        
        Args:
            secret_key: Clave secreta para firmar los tokens
            algorithm: Algoritmo de encriptación (por defecto HS256)
        """
        self.secret_key = secret_key
        self.algorithm = algorithm
    
    def create_token(
        self, 
        data: Dict[str, Any], 
        expires_delta: Optional[timedelta] = None
    ) -> str:
        """
        Crea un token JWT
        
        Args:
            data: Datos a incluir en el payload del token
            expires_delta: Tiempo de expiración del token (opcional)
            
        Returns:
            Token JWT codificado como string
        """
        to_encode = data.copy()
        
        if expires_delta:
            expire = datetime.utcnow() + expires_delta
        else:
            # Por defecto expira en 24 horas
            expire = datetime.utcnow() + timedelta(hours=24)
        
        to_encode.update({"exp": expire})
        
        encoded_jwt = jwt.encode(
            to_encode, 
            self.secret_key, 
            algorithm=self.algorithm
        )
        
        return encoded_jwt
    
    def verify_token(self, token: str) -> Optional[Dict[str, Any]]:
        """
        Verifica y decodifica un token JWT
        
        Args:
            token: Token JWT a verificar
            
        Returns:
            Payload del token si es válido, None si es inválido o expirado
        """
        try:
            payload = jwt.decode(
                token, 
                self.secret_key, 
                algorithms=[self.algorithm]
            )
            return payload
        except jwt.ExpiredSignatureError:
            # Token expirado
            return None
        except jwt.InvalidTokenError:
            # Token inválido
            return None
    
    def decode_token_without_verification(self, token: str) -> Optional[Dict[str, Any]]:
        """
        Decodifica un token sin verificar su firma (útil para debugging)
        
        Args:
            token: Token JWT a decodificar
            
        Returns:
            Payload del token sin verificar
        """
        try:
            payload = jwt.decode(
                token, 
                options={"verify_signature": False}
            )
            return payload
        except jwt.InvalidTokenError:
            return None
