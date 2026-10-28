"""guardar_imagen / borrar_imagen: formatos permitidos, tamaño y limpieza."""
import base64

import pytest

from services import imagen_service
from services.imagen_service import borrar_imagen, guardar_imagen

PNG = b"\x89PNG\r\n\x1a\n" + b"0" * 32
JPG = b"\xff\xd8\xff" + b"0" * 32
WEBP = b"RIFF" + b"0000" + b"WEBP" + b"0" * 32


def _b64(raw: bytes) -> str:
    return base64.b64encode(raw).decode()


@pytest.fixture(autouse=True)
def carpeta_temporal(tmp_path, monkeypatch):
    monkeypatch.setattr(imagen_service, "UPLOAD_DIR", tmp_path)
    return tmp_path


@pytest.mark.parametrize("raw,ext", [(PNG, "png"), (JPG, "jpg"), (WEBP, "webp")])
def test_guarda_formatos_permitidos(carpeta_temporal, raw, ext):
    ruta = guardar_imagen(_b64(raw))
    assert ruta.startswith("/uploads/") and ruta.endswith(f".{ext}")
    assert (carpeta_temporal / ruta.rsplit("/", 1)[1]).read_bytes() == raw


def test_acepta_data_url(carpeta_temporal):
    ruta = guardar_imagen(f"data:image/png;base64,{_b64(PNG)}")
    assert ruta.endswith(".png")


def test_rechaza_formato_no_permitido():
    with pytest.raises(ValueError, match="Formato"):
        guardar_imagen(_b64(b"<script>alert(1)</script>"))


def test_rechaza_base64_invalido():
    with pytest.raises(ValueError, match="no es válida"):
        guardar_imagen("%%%no-b64")


def test_rechaza_imagen_muy_grande():
    with pytest.raises(ValueError, match="5MB"):
        guardar_imagen(_b64(PNG + b"0" * imagen_service.MAX_BYTES))


def test_borrar_imagen(carpeta_temporal):
    ruta = guardar_imagen(_b64(PNG))
    archivo = carpeta_temporal / ruta.rsplit("/", 1)[1]
    assert archivo.exists()
    borrar_imagen(ruta)
    assert not archivo.exists()


@pytest.mark.parametrize("ruta", [None, "", "http://externa/x.png", "/otra/ruta.png"])
def test_borrar_imagen_ignora_rutas_ajenas(ruta):
    borrar_imagen(ruta)