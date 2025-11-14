from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from typing import Generator
import os
from dotenv import load_dotenv

# Cargar variables de entorno
load_dotenv()

# Obtener URL de la base de datos desde el archivo .env
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./inventario.db")

# Crear el motor de la base de datos
engine = create_engine(
    DATABASE_URL,
    connect_args={"check_same_thread": False} if "sqlite" in DATABASE_URL else {},
    echo=os.getenv("DEBUG", "False").lower() == "true"
)

# Crear la sesión local
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Dependencia para obtener la sesión de base de datos
def get_db() -> Generator[Session, None, None]:
    """
    Generador que proporciona una sesión de base de datos.
    Se usa como dependencia en los endpoints de FastAPI.
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# Función para crear todas las tablas
def create_tables():
    """
    Crea todas las tablas definidas en los modelos.
    """
    from app.database.models import Base
    Base.metadata.create_all(bind=engine)

# Función para eliminar todas las tablas
def drop_tables():
    """
    Elimina todas las tablas de la base de datos.
    ¡Usar con precaución!
    """
    from app.database.models import Base
    Base.metadata.drop_all(bind=engine)
