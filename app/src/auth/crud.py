from sqlalchemy.orm import Session
from typing import Optional
from datetime import datetime
from app.database.models import Usuario
from app.database.crud import CRUDBase
from app.database.schemas import UsuarioCreate, UsuarioUpdate
from app.src.auth.password import PasswordHandler


class CRUDUsuario(CRUDBase[Usuario, UsuarioCreate, UsuarioUpdate]):
    """CRUD específico para usuarios con funcionalidades de autenticación"""
    
    def get_by_email(self, db: Session, email: str) -> Optional[Usuario]:
        """
        Obtiene un usuario por su email
        
        Args:
            db: Sesión de base de datos
            email: Email del usuario
            
        Returns:
            Usuario encontrado o None
        """
        return db.query(Usuario).filter(Usuario.email == email).first()
    
    def get_by_username(self, db: Session, username: str) -> Optional[Usuario]:
        """
        Obtiene un usuario por su username
        
        Args:
            db: Sesión de base de datos
            username: Nombre de usuario
            
        Returns:
            Usuario encontrado o None
        """
        return db.query(Usuario).filter(Usuario.username == username).first()
    
    def create(self, db: Session, *, obj_in: UsuarioCreate) -> Usuario:
        """
        Crea un nuevo usuario con la contraseña hasheada
        
        Args:
            db: Sesión de base de datos
            obj_in: Datos del usuario a crear
            
        Returns:
            Usuario creado
        """
        # Convertir el objeto Pydantic a diccionario
        obj_in_data = obj_in.model_dump()
        
        # Extraer y hashear la contraseña
        password = obj_in_data.pop("password")
        hashed_password = PasswordHandler.hash_password(password)
        
        # Crear el usuario con el password hasheado
        db_obj = Usuario(
            **obj_in_data,
            password_hash=hashed_password
        )
        
        db.add(db_obj)
        db.commit()
        db.refresh(db_obj)
        return db_obj
    
    def authenticate(self, db: Session, email: str, password: str) -> Optional[Usuario]:
        """
        Autentica un usuario con email y contraseña
        
        Args:
            db: Sesión de base de datos
            email: Email del usuario
            password: Contraseña en texto plano
            
        Returns:
            Usuario si la autenticación es exitosa, None en caso contrario
        """
        usuario = self.get_by_email(db, email=email)
        
        if not usuario:
            return None
        
        if not PasswordHandler.verify_password(password, usuario.password_hash):
            return None
        
        return usuario
    
    def update_last_access(self, db: Session, usuario_id: int) -> Usuario:
        """
        Actualiza la fecha de último acceso del usuario
        
        Args:
            db: Sesión de base de datos
            usuario_id: ID del usuario
            
        Returns:
            Usuario actualizado
        """
        usuario = self.get_or_404(db, usuario_id)
        usuario.fecha_ultimo_acceso = datetime.utcnow()
        db.add(usuario)
        db.commit()
        db.refresh(usuario)
        return usuario
    
    def change_password(
        self, 
        db: Session, 
        usuario_id: int, 
        current_password: str, 
        new_password: str
    ) -> bool:
        """
        Cambia la contraseña de un usuario verificando la actual
        
        Args:
            db: Sesión de base de datos
            usuario_id: ID del usuario
            current_password: Contraseña actual
            new_password: Nueva contraseña
            
        Returns:
            True si el cambio fue exitoso, False en caso contrario
        """
        usuario = self.get_or_404(db, usuario_id)
        
        # Verificar contraseña actual
        if not PasswordHandler.verify_password(current_password, usuario.password_hash):
            return False
        
        # Actualizar con la nueva contraseña hasheada
        usuario.password_hash = PasswordHandler.hash_password(new_password)
        db.add(usuario)
        db.commit()
        return True
    
    def reset_password(self, db: Session, email: str, new_password: str) -> bool:
        """
        Resetea la contraseña de un usuario (sin verificar la actual)
        Útil para recuperación de contraseña
        
        Args:
            db: Sesión de base de datos
            email: Email del usuario
            new_password: Nueva contraseña
            
        Returns:
            True si el reseteo fue exitoso, False si no se encontró el usuario
        """
        usuario = self.get_by_email(db, email=email)
        
        if not usuario:
            return False
        
        usuario.password_hash = PasswordHandler.hash_password(new_password)
        db.add(usuario)
        db.commit()
        return True
    
    def is_active(self, usuario: Usuario) -> bool:
        """
        Verifica si un usuario está activo
        
        Args:
            usuario: Usuario a verificar
            
        Returns:
            True si el estado del usuario está activo
        """
        # Asumiendo que existe un estado "activo" con nombre "Activo"
        if usuario.estado_usuario:
            return usuario.estado_usuario.activo
        return False


# Instancia del CRUD de usuarios
crud_usuario = CRUDUsuario(Usuario)
