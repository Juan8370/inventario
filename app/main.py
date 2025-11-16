import logging
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.exception_handlers import register_exception_handlers
from app.core.logging import setup_logging
from app.core.settings import get_settings
from app.database.database import create_tables, SessionLocal
from app.database.init_data import inicializar_datos_desarrollo
from app.routers import auth as auth_router
from app.routers import empresas as empresas_router
from app.routers import productos as productos_router
from app.routers import system as system_router
from app.routers import usuarios as usuarios_router
from app.routers import stats as stats_router


settings = get_settings()

# Configure logging first
setup_logging(settings)
logger = logging.getLogger(__name__)

# FastAPI app
app = FastAPI(
    title=settings.APP_NAME,
    description=settings.APP_DESCRIPTION,
    version=settings.APP_VERSION,
    debug=settings.DEBUG,
)

# CORS
allowed_origins = [str(o) for o in settings.ALLOWED_ORIGINS]
app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Routers
app.include_router(system_router.router)
app.include_router(auth_router.router)
app.include_router(productos_router.router)
app.include_router(empresas_router.router)
app.include_router(usuarios_router.router)
app.include_router(stats_router.router)

# Exception handlers
register_exception_handlers(app)


@app.on_event("startup")
async def startup_event():
    # Create tables only for dev/test environments
    if settings.ENVIRONMENT != "production":
        create_tables()
        logger.info("Base de datos inicializada correctamente")

    # Seed development data when allowed
    if settings.ENVIRONMENT == "development":
        db = SessionLocal()
        try:
            inicializar_datos_desarrollo(db)
        except Exception as e:  # noqa: BLE001
            logger.warning("Error inicializando datos de desarrollo", exc_info=e)
        finally:
            db.close()