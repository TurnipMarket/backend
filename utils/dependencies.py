from fastapi import Depends, HTTPException
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session

from database.connection import get_db
from models.usuario import Usuario
from utils.auth_token import leer_token

_bearer = HTTPBearer(auto_error=False)


def get_current_user(
    creds: HTTPAuthorizationCredentials | None = Depends(_bearer),
    db: Session = Depends(get_db),
) -> Usuario:
    """Usuario logueado y verificado, a partir del header Authorization: Bearer <token>."""
    if creds is None:
        raise HTTPException(status_code=401, detail="Necesitás iniciar sesión")
    usuario_id = leer_token(creds.credentials)
    usuario = db.get(Usuario, usuario_id) if usuario_id is not None else None
    if usuario is None:
        raise HTTPException(status_code=401, detail="Sesión inválida o vencida")
    if not usuario.verificado:
        raise HTTPException(status_code=403, detail="Verificá tu cuenta para publicar")
    return usuario
