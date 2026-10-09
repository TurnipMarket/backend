"""Guarda en disco las imágenes de productos que llegan como base64."""
import base64
import binascii
import os
import uuid
from pathlib import Path

from database.connection import DATABASE_PATH

# Por defecto queda junto a la base de datos (así entra en el mismo volumen de Docker).
UPLOAD_DIR = Path(os.getenv("UPLOAD_DIR", str(Path(DATABASE_PATH).parent / "uploads")))
MAX_BYTES = 5 * 1024 * 1024


def _extension(raw: bytes) -> str | None:
    # Se detecta por el contenido real, no por lo que declare el cliente.
    if raw.startswith(b"\xff\xd8\xff"):
        return "jpg"
    if raw.startswith(b"\x89PNG\r\n\x1a\n"):
        return "png"
    if raw[:4] == b"RIFF" and raw[8:12] == b"WEBP":
        return "webp"
    return None


def guardar_imagen(imagen_b64: str) -> str:
    """Acepta 'data:image/png;base64,XXXX' o base64 puro. Devuelve la ruta pública '/uploads/<archivo>'."""
    datos = imagen_b64.split(",", 1)[1] if imagen_b64.startswith("data:") and "," in imagen_b64 else imagen_b64
    try:
        raw = base64.b64decode(datos, validate=True)
    except (binascii.Error, ValueError):
        raise ValueError("La imagen no es válida")
    if len(raw) > MAX_BYTES:
        raise ValueError("La imagen debe ser menor a 5MB")
    ext = _extension(raw)
    if ext is None:
        raise ValueError("Formato de imagen no permitido (JPG, PNG o WebP)")

    UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
    nombre = f"{uuid.uuid4().hex}.{ext}"
    (UPLOAD_DIR / nombre).write_bytes(raw)
    return f"/uploads/{nombre}"


def borrar_imagen(ruta_publica: str | None) -> None:
    if not ruta_publica or not ruta_publica.startswith("/uploads/"):
        return
    (UPLOAD_DIR / Path(ruta_publica).name).unlink(missing_ok=True)
