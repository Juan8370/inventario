from typing import Any

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.core.settings import get_settings
from app.database.database import get_db
from app.database.models import Base, Usuario
from app.src.auth import get_current_admin


router = APIRouter(tags=["system"])


@router.get("/", status_code=200)
async def root() -> dict[str, Any]:
    settings = get_settings()
    return {
        "message": "Bienvenido al Sistema de Inventario",
        "version": settings.APP_VERSION,
        "docs": "/docs",
        "redoc": "/redoc",
    }


@router.get("/health", status_code=200)
async def health_check(db: Session = Depends(get_db)) -> dict[str, Any]:
    settings = get_settings()
    try:
        db.execute(text("SELECT 1"))
        db_status = "conectada"
    except Exception:
        raise HTTPException(status_code=503, detail="Error de conexión con la base de datos")

    return {
        "status": "OK",
        "message": "API funcionando correctamente",
        "database": db_status,
        "environment": settings.ENVIRONMENT,
    }


@router.get("/db/info", status_code=200)
async def database_info(current_user: Usuario = Depends(get_current_admin)) -> dict[str, Any]:
    settings = get_settings()
    return {
        "database_url": settings.DATABASE_URL.split("@")[-1],
        "tables": list(Base.metadata.tables.keys()),
        "total_tables": len(Base.metadata.tables),
    }


# (la ruta /stats fue movida al router stats)
