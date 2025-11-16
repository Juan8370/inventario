from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.database.database import get_db
from app.database import schemas
from app.database.models import Usuario
from app.src.auth import (
    auth_service,
    LoginRequest,
    get_current_user,
    ChangePasswordRequest,
    crud_usuario as auth_crud_usuario,
)


router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/login", status_code=200)
async def login(login_data: LoginRequest, db: Session = Depends(get_db)):
    return auth_service.login(db=db, login_data=login_data)


@router.get("/me", response_model=schemas.Usuario, status_code=200)
async def get_my_profile(current_user: Usuario = Depends(get_current_user)):
    return current_user


@router.post("/change-password", status_code=200)
async def change_password(
    password_data: ChangePasswordRequest,
    current_user: Usuario = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    success = auth_crud_usuario.change_password(
        db=db,
        usuario_id=current_user.id,
        current_password=password_data.current_password,
        new_password=password_data.new_password,
    )

    if not success:
        from fastapi import HTTPException

        raise HTTPException(status_code=400, detail="Contraseña actual incorrecta")

    return {"message": "Contraseña actualizada exitosamente"}
