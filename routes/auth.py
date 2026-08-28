from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from sqlalchemy.orm import Session
from Back_Opecode.database.connection import get_db
from Back_Opecode.services.auth_service import (
    registrar_usuario,
    login_usuario,
    verificar_disponibilidad,
)

router = APIRouter(prefix="/api/auth", tags=["auth"])


class ClientInfo(BaseModel):
    origin: str | None = None
    timestamp: str | None = None


class RegistroRequest(BaseModel):
    username: str
    email: str
    phone: str | None = None
    password: str
    verifyBy: str = "email"
    client: ClientInfo | None = None


class LoginRequest(BaseModel):
    identifier: str
    password: str
    remember: bool = False
    client: ClientInfo | None = None


@router.post("/register", status_code=201)
def register(req: RegistroRequest, db: Session = Depends(get_db)):
    try:
        usuario = registrar_usuario(db, req.username, req.email, req.phone, req.password)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    return {
        "mensaje": "Usuario registrado. Revisa tu email para el código de verificación.",
        "usuario_id": usuario.id,
        "username": usuario.username,
        "verificado": usuario.verificado,
        "verifyBy": req.verifyBy,
    }


@router.post("/login")
def login(req: LoginRequest, db: Session = Depends(get_db)):
    try:
        resultado = login_usuario(db, req.identifier, req.password)
    except ValueError as e:
        raise HTTPException(status_code=403, detail=str(e))
    if resultado is None:
        raise HTTPException(status_code=401, detail="Email o contraseña incorrectos")
    return {"sesion": "iniciada", "remember": req.remember, **resultado}


@router.get("/availability")
def availability(
    field: str = Query(...),
    value: str = Query(...),
    db: Session = Depends(get_db),
):
    try:
        disponible = verificar_disponibilidad(db, field, value)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    return {"available": disponible}