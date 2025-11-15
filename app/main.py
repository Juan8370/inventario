from fastapi import FastAPI, Depends, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from dotenv import load_dotenv
import os
from sqlalchemy import text

from app.database.database import get_db, create_tables, engine
from app.database.models import Base, Producto, Usuario, Empresa
from app.database.crud import CRUDBase
from app.database import schemas
from app.database.init_data import inicializar_datos_desarrollo
from app.src.auth import (
    auth_service,
    LoginRequest,
    get_current_user,
    get_current_admin,
    get_optional_user,
    ChangePasswordRequest,
    crud_usuario as auth_crud_usuario
)

# Cargar variables de entorno
load_dotenv()

# Crear instancia de FastAPI
app = FastAPI(
    title=os.getenv("APP_NAME", "Sistema de Inventario"),
    description=os.getenv("APP_DESCRIPTION", "API para gestión de inventario"),
    version=os.getenv("APP_VERSION", "1.0.0"),
    debug=os.getenv("DEBUG", "False").lower() == "true"
)

# Configurar CORS
allowed_origins = os.getenv("ALLOWED_ORIGINS", "http://localhost:3000").split(",")
app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Crear las tablas en la base de datos al iniciar la aplicación
@app.on_event("startup")
async def startup_event():
    """Evento que se ejecuta al iniciar la aplicación"""
    create_tables()
    print("✓ Base de datos inicializada correctamente")
    
    # Inicializar datos de desarrollo
    from app.database.database import SessionLocal
    db = SessionLocal()
    try:
        inicializar_datos_desarrollo(db)
    except Exception as e:
        print(f"⚠️  Error inicializando datos de desarrollo: {e}")
    finally:
        db.close()

# Instancias CRUD
crud_producto = CRUDBase[Producto, schemas.ProductoCreate, schemas.ProductoUpdate](Producto)
crud_usuario = CRUDBase[Usuario, schemas.UsuarioCreate, schemas.UsuarioUpdate](Usuario)
crud_empresa = CRUDBase[Empresa, schemas.EmpresaCreate, schemas.EmpresaUpdate](Empresa)

# ===== ENDPOINTS DE VERIFICACIÓN =====

@app.get("/", status_code=200)
async def root():
    """Endpoint raíz de bienvenida"""
    return {
        "message": "Bienvenido al Sistema de Inventario",
        "version": os.getenv("APP_VERSION", "1.0.0"),
        "docs": "/docs",
        "redoc": "/redoc"
    }

@app.get("/health", status_code=200)
async def health_check(db: Session = Depends(get_db)):
    """Verificar el estado de la API y la conexión a la base de datos"""
    try:
        # Intentar hacer una consulta simple para verificar la conexión
        db.execute(text("SELECT 1"))
        db_status = "conectada"
    except Exception as e:
        db_status = f"error: {str(e)}"
        raise HTTPException(status_code=503, detail="Error de conexión con la base de datos")
    
    return {
        "status": "OK",
        "message": "API funcionando correctamente",
        "database": db_status,
        "environment": os.getenv("ENVIRONMENT", "production")
    }

@app.get("/db/info", status_code=200)
async def database_info(current_user: Usuario = Depends(get_current_admin)):
    """Obtener información de la base de datos (Solo administradores)"""
    return {
        "database_url": os.getenv("DATABASE_URL", "sqlite:///./inventario.db").split("@")[-1],  # Ocultar credenciales
        "tables": list(Base.metadata.tables.keys()),
        "total_tables": len(Base.metadata.tables)
    }

# ===== ENDPOINTS DE AUTENTICACIÓN =====

@app.post("/auth/login", status_code=200)
async def login(login_data: LoginRequest, db: Session = Depends(get_db)):
    """Autenticar usuario con email y contraseña"""
    return auth_service.login(db=db, login_data=login_data)

@app.get("/auth/me", response_model=schemas.Usuario, status_code=200)
async def get_my_profile(current_user: Usuario = Depends(get_current_user)):
    """Obtener perfil del usuario autenticado"""
    return current_user

@app.post("/auth/change-password", status_code=200)
async def change_password(
    password_data: ChangePasswordRequest,
    current_user: Usuario = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Cambiar contraseña del usuario actual"""
    success = auth_crud_usuario.change_password(
        db=db,
        usuario_id=current_user.id,
        current_password=password_data.current_password,
        new_password=password_data.new_password
    )
    
    if not success:
        raise HTTPException(status_code=400, detail="Contraseña actual incorrecta")
    
    return {"message": "Contraseña actualizada exitosamente"}

# ===== ENDPOINTS DE PRODUCTOS =====

@app.get("/productos", response_model=list[schemas.Producto], status_code=200)
async def listar_productos(
    skip: int = Query(0, ge=0),
    limit: int = Query(10, ge=1),
    db: Session = Depends(get_db),
    current_user: Usuario | None = Depends(get_optional_user)
):
    """Listar todos los productos con paginación (público con autenticación opcional)"""
    productos = crud_producto.get_multi(db, skip=skip, limit=limit)
    return productos

@app.get("/productos/{producto_id}", response_model=schemas.Producto, status_code=200)
async def obtener_producto(
    producto_id: int,
    db: Session = Depends(get_db),
    current_user: Usuario | None = Depends(get_optional_user)
):
    """Obtener un producto por su ID (público con autenticación opcional)"""
    return crud_producto.get_or_404(db, producto_id)

@app.post("/productos", response_model=schemas.Producto, status_code=201)
async def crear_producto(
    producto: schemas.ProductoCreate,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user)
):
    """Crear un nuevo producto (requiere autenticación)"""
    # Verificar que no exista un producto con el mismo código
    producto_existente = crud_producto.get_by_field(db, "codigo", producto.codigo)
    if producto_existente:
        raise HTTPException(status_code=400, detail="Ya existe un producto con este código")
    
    return crud_producto.create(db, obj_in=producto)

@app.put("/productos/{producto_id}", response_model=schemas.Producto, status_code=200)
async def actualizar_producto(
    producto_id: int,
    producto: schemas.ProductoUpdate,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user)
):
    """Actualizar un producto existente (requiere autenticación)"""
    db_producto = crud_producto.get_or_404(db, producto_id)
    return crud_producto.update(db, db_obj=db_producto, obj_in=producto)

@app.delete("/productos/{producto_id}", status_code=200)
async def eliminar_producto(
    producto_id: int,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_admin)
):
    """Eliminar un producto (solo administradores)"""
    producto = crud_producto.delete(db, id=producto_id)
    return {"message": f"Producto {producto.nombre} eliminado correctamente"}

@app.get("/productos/buscar/{termino}", status_code=200)
async def buscar_productos(
    termino: str,
    skip: int = Query(0, ge=0),
    limit: int = Query(10, ge=1),
    db: Session = Depends(get_db),
    current_user: Usuario | None = Depends(get_optional_user)
):
    """Buscar productos por nombre, código o descripción (público con autenticación opcional)"""
    productos = crud_producto.search(
        db,
        search_fields=["nombre", "codigo", "descripcion", "marca"],
        search_term=termino,
        skip=skip,
        limit=limit
    )
    return productos

# ===== ENDPOINTS DE EMPRESAS =====

@app.get("/empresas", response_model=list[schemas.Empresa], status_code=200)
async def listar_empresas(
    skip: int = Query(0, ge=0),
    limit: int = Query(10, ge=1),
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user)
):
    """Listar todas las empresas con paginación (requiere autenticación)"""
    empresas = crud_empresa.get_multi(db, skip=skip, limit=limit)
    return empresas

@app.post("/empresas", response_model=schemas.Empresa, status_code=201)
async def crear_empresa(
    empresa: schemas.EmpresaCreate,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_admin)
):
    """Crear una nueva empresa (solo administradores)"""
    # Verificar que no exista una empresa con el mismo RUC
    empresa_existente = crud_empresa.get_by_field(db, "ruc", empresa.ruc)
    if empresa_existente:
        raise HTTPException(status_code=400, detail="Ya existe una empresa con este RUC")
    
    return crud_empresa.create(db, obj_in=empresa)

# ===== ENDPOINTS DE USUARIOS =====

@app.get("/usuarios", response_model=list[schemas.Usuario], status_code=200)
async def listar_usuarios(
    skip: int = Query(0, ge=0),
    limit: int = Query(10, ge=1),
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_admin)
):
    """Listar todos los usuarios (solo administradores)"""
    usuarios = crud_usuario.get_multi(db, skip=skip, limit=limit)
    return usuarios

@app.post("/usuarios", response_model=schemas.Usuario, status_code=201)
async def crear_usuario(
    usuario: schemas.UsuarioCreate,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_admin)
):
    """Crear un nuevo usuario (solo administradores)"""
    # Verificar que no exista un usuario con el mismo email o username
    if auth_crud_usuario.get_by_email(db, usuario.email):
        raise HTTPException(status_code=400, detail="Ya existe un usuario con este email")
    
    if auth_crud_usuario.get_by_username(db, usuario.username):
        raise HTTPException(status_code=400, detail="Ya existe un usuario con este username")
    
    return auth_crud_usuario.create(db, obj_in=usuario)

# ===== ENDPOINTS DE ESTADÍSTICAS =====

@app.get("/stats", status_code=200)
async def obtener_estadisticas(
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user)
):
    """Obtener estadísticas generales del sistema (requiere autenticación)"""
    total_productos = crud_producto.count(db)
    total_empresas = crud_empresa.count(db)
    total_usuarios = crud_usuario.count(db)
    
    return {
        "total_productos": total_productos,
        "total_empresas": total_empresas,
        "total_usuarios": total_usuarios,
        "database_connected": True,
        "usuario_actual": current_user.username
    }