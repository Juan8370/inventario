"""
Inicialización de datos por defecto para desarrollo
"""
from sqlalchemy.orm import Session
from app.database.models import TipoUsuario, EstadoUsuario, Usuario
from app.src.auth import crud_usuario
from app.database.schemas import UsuarioCreate
import os


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
    # Solo crear en modo desarrollo
    if os.getenv("ENVIRONMENT", "development") != "development":
        return
    
    # Verificar si ya existe el usuario admin
    admin_existente = crud_usuario.get_by_username(db, "admin")
    if admin_existente:
        print("✓ Usuario admin ya existe")
        return
    
    # Obtener tipo y estado de usuario
    tipo_admin = db.query(TipoUsuario).filter(
        TipoUsuario.nombre == "Administrador"
    ).first()
    
    estado_activo = db.query(EstadoUsuario).filter(
        EstadoUsuario.nombre == "Activo"
    ).first()
    
    if not tipo_admin or not estado_activo:
        print("✗ No se pudieron obtener tipo y estado de usuario")
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
        print("✓ Usuario admin creado exitosamente")
        print("  Username: admin")
        print("  Email: admin@ejemplo.com")
        print("  Password: admin123")
        print("  ⚠️  CAMBIAR CONTRASEÑA EN PRODUCCIÓN")
    except Exception as e:
        print(f"✗ Error creando usuario admin: {e}")


def inicializar_datos_desarrollo(db: Session):
    """Inicializar todos los datos por defecto para desarrollo"""
    print("\n🔄 Inicializando datos de desarrollo...")
    
    crear_tipos_usuario_default(db)
    crear_estados_usuario_default(db)
    crear_usuario_admin_default(db)
    
    print("✓ Inicialización de datos completada\n")
