"""Tokens de sesión (JWT HS256) para el login."""
import os
from datetime import datetime, timedelta, timezone

import jwt

ALGORITHM = "HS256"
TTL_NORMAL = timedelta(hours=8)
TTL_RECORDAR = timedelta(days=7)


def _secret() -> str:
    secret = os.getenv("JWT_SECRET", "")
    if len(secret) < 32:
        raise RuntimeError("Falta JWT_SECRET en el .env (mínimo 32 caracteres)")
    return secret


def crear_token(usuario_id: int, recordar: bool = False) -> tuple[str, int]:
    """Devuelve (token, expiración en segundos unix)."""
    exp = datetime.now(timezone.utc) + (TTL_RECORDAR if recordar else TTL_NORMAL)
    token = jwt.encode({"sub": str(usuario_id), "exp": exp}, _secret(), algorithm=ALGORITHM)
    return token, int(exp.timestamp())


def leer_token(token: str) -> int | None:
    """Devuelve el id de usuario, o None si el token es inválido o venció."""
    try:
        payload = jwt.decode(token, _secret(), algorithms=[ALGORITHM])
        return int(payload["sub"])
    except (jwt.PyJWTError, KeyError, ValueError):
        return None
