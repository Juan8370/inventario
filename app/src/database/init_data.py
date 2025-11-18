"""
Inicialización de datos por defecto para desarrollo
"""
import logging
from sqlalchemy.orm import Session
from app.src.database.models import TipoUsuario, EstadoUsuario, Usuario, TipoLog, TipoTransaccion
from app.src.auth import crud_usuario
from app.src.database.schemas import UsuarioCreate
from app.src.core.settings import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()


def crear_tipos_usuario_default(db: Session):
    """Crear tipos de usuario por defecto si no existen"""
    tipos_default = [
        {"nombre": "Administrador", "descripcion": "Usuario con acceso total al sistema"},
        {"nombre": "Usuario", "descripcion": "Usuario estándar del sistema"},
    ]
    
    for tipo_data in tipos_default:
        tipo_existente = db.query(TipoUsuario).filter(
            TipoUsuario.nombre == tipo_data["nombre"]
        ).first()
        
        if not tipo_existente:
            nuevo_tipo = TipoUsuario(**tipo_data)
            db.add(nuevo_tipo)
    
    db.commit()


def crear_tipos_log_default(db: Session):
    """Crear tipos de log por defecto si no existen"""
    tipos_default = [
        {"nombre": "ERROR", "descripcion": "Errores críticos en la aplicación"},
        {"nombre": "WARNING", "descripcion": "Errores de advertencias no críticos"},
        {"nombre": "INFO", "descripcion": "Información sobre las acciones"},
        {"nombre": "LOGIN", "descripcion": "Inicio de sesión de usuario"},
        {"nombre": "SIGNUP", "descripcion": "Usuario creado"},
    ]
    
    for tipo_data in tipos_default:
        tipo_existente = db.query(TipoLog).filter(
            TipoLog.nombre == tipo_data["nombre"]
        ).first()
        
        if not tipo_existente:
            nuevo_tipo = TipoLog(**tipo_data)
            db.add(nuevo_tipo)
    
    db.commit()


def crear_tipos_transaccion_default(db: Session):
    """Crear tipos de transacción por defecto si no existen"""
    tipos_default = [
        {"nombre": "ENTRADA", "descripcion": "Entrada de productos al inventario"},
        {"nombre": "SALIDA", "descripcion": "Salida de productos del inventario"},
    ]
    
    for tipo_data in tipos_default:
        tipo_existente = db.query(TipoTransaccion).filter(
            TipoTransaccion.nombre == tipo_data["nombre"]
        ).first()
        
        if not tipo_existente:
            nuevo_tipo = TipoTransaccion(**tipo_data)
            db.add(nuevo_tipo)
    
    db.commit()


def crear_estados_usuario_default(db: Session):
    """Crear estados de usuario por defecto si no existen"""
    estados_default = [
        {"nombre": "Activo", "descripcion": "Usuario activo en el sistema"},
        {"nombre": "Inactivo", "descripcion": "Usuario inactivo"},
    ]
    
    for estado_data in estados_default:
        estado_existente = db.query(EstadoUsuario).filter(
            EstadoUsuario.nombre == estado_data["nombre"]
        ).first()
        
        if not estado_existente:
            nuevo_estado = EstadoUsuario(**estado_data)
            db.add(nuevo_estado)
    
    db.commit()


def crear_usuario_admin_default(db: Session):
    """Crear usuario admin por defecto para desarrollo"""
    # Solo crear en modo desarrollo y cuando la bandera lo permita
    if settings.ENVIRONMENT != "development" or not settings.SEED_DEV_ADMIN:
        return
    
    # Verificar si ya existe el usuario admin
    admin_existente = crud_usuario.get_by_username(db, "admin")
    if admin_existente:
        logger.info("Usuario admin ya existe")
        return
    
    # Obtener tipo y estado de usuario
    tipo_admin = db.query(TipoUsuario).filter(
        TipoUsuario.nombre == "Administrador"
    ).first()
    
    estado_activo = db.query(EstadoUsuario).filter(
        EstadoUsuario.nombre == "Activo"
    ).first()
    
    if not tipo_admin or not estado_activo:
        logger.warning("No se pudieron obtener tipo y estado de usuario")
        return
    
    # Crear usuario admin
    admin_data = UsuarioCreate(
        username="admin",
        email="admin@ejemplo.com",
        password="admin123",  # Contraseña por defecto para desarrollo
        nombre="Administrador",
        apellido="Sistema",
        tipo_usuario_id=tipo_admin.id,
        estado_usuario_id=estado_activo.id
    )
    
    try:
        crud_usuario.create(db, obj_in=admin_data)
        logger.info("Usuario admin creado exitosamente | Username=admin | Email=admin@ejemplo.com")
    except Exception as e:  # noqa: BLE001
        logger.exception("Error creando usuario admin: %s", e)


def inicializar_datos_desarrollo(db: Session):
    """Inicializar todos los datos por defecto para desarrollo"""
    logger.info("Inicializando datos de desarrollo...")

    crear_tipos_usuario_default(db)
    crear_estados_usuario_default(db)
    crear_tipos_log_default(db)
    crear_tipos_transaccion_default(db)
    crear_usuario_admin_default(db)

    logger.info("Inicialización de datos completada")
