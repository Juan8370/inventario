from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from typing import Generator

from app.src.core.settings import get_settings

settings = get_settings()

DATABASE_URL = settings.DATABASE_URL

engine = create_engine(
    DATABASE_URL,
    connect_args={"check_same_thread": False} if "sqlite" in DATABASE_URL else {},
    echo=bool(settings.DEBUG),
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
    from app.src.database.models import Base
    Base.metadata.create_all(bind=engine)

# Función para eliminar todas las tablas
def drop_tables():
    """
    Elimina todas las tablas de la base de datos.
    ¡Usar con precaución!
    """
    from app.src.database.models import Base
    Base.metadata.drop_all(bind=engine)
