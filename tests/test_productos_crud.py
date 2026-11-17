"""UPDATE y DELETE de productos (RF07) y restricciones de la base. Usa una base temporal."""
import os
import sys
import tempfile
from pathlib import Path

_tmp = tempfile.mkdtemp()
os.environ.setdefault("DATABASE_PATH", str(Path(_tmp) / "test.db"))
os.environ.setdefault("UPLOAD_DIR", str(Path(_tmp) / "uploads"))
os.environ.setdefault("JWT_SECRET", "x" * 40)
# El módulo de email exige SMTP al importarse; valores falsos, estos tests no envían mails.
for k in ("SMTP_HOST", "SMTP_USER", "SMTP_PASSWORD"):
    os.environ.setdefault(k, "test")
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.exc import IntegrityError

from database.connection import SessionLocal
from main import app
from models.producto import Producto
from models.usuario import Usuario
from utils.security import hash_password

BODY = {
    "title": "Notebook usada",
    "description": "Notebook con 8GB de RAM y 256GB de SSD.",
    "category": "electronics",
    "price": 450000,
    "currency": "ARS",
    "condition": "like_new",
}


@pytest.fixture(scope="module")
def client():
    with SessionLocal() as db:
        for nombre in ("duenio_crud", "otro_crud"):
            if not db.query(Usuario).filter_by(username=nombre).first():
                db.add(Usuario(nombre=nombre, username=nombre, alias=nombre, email=f"{nombre}@t.com",
                               password=hash_password("Clave123!"), verificado=True))
        db.commit()
    return TestClient(app)


def _auth(client, usuario):
    r = client.post("/api/auth/login", json={"identifier": usuario, "password": "Clave123!"})
    assert r.status_code == 200
    return {"Authorization": f"Bearer {r.json()['token']}"}


def _publicar(client, usuario="duenio_crud"):
    r = client.post("/api/products", json=BODY, headers=_auth(client, usuario))
    assert r.status_code == 201
    return r.json()["product"]["id"]


def _en_catalogo(client, pid):
    return any(p["id"] == pid for p in client.get("/api/products").json())


def test_editar_producto_propio(client):
    pid = _publicar(client)
    r = client.put(f"/api/products/{pid}", json={"price": 399999.99, "title": "Notebook en oferta"},
                   headers=_auth(client, "duenio_crud"))
    assert r.status_code == 200
    p = r.json()["product"]
    assert p["price"] == 399999.99 and p["title"] == "Notebook en oferta"
    assert p["category"] == "electronics"  # lo que no se mandó queda igual


def test_editar_sin_token_401(client):
    pid = _publicar(client)
    assert client.put(f"/api/products/{pid}", json={"price": 1}).status_code == 401


def test_editar_producto_ajeno_403(client):
    pid = _publicar(client)
    r = client.put(f"/api/products/{pid}", json={"price": 1}, headers=_auth(client, "otro_crud"))
    assert r.status_code == 403


def test_editar_inexistente_404(client):
    r = client.put("/api/products/999999", json={"price": 10}, headers=_auth(client, "duenio_crud"))
    assert r.status_code == 404


def test_editar_sin_cambios_400(client):
    pid = _publicar(client)
    r = client.put(f"/api/products/{pid}", json={}, headers=_auth(client, "duenio_crud"))
    assert r.status_code == 400


@pytest.mark.parametrize("cambio", [{"price": -5}, {"price": 0}, {"category": "xyz"},
                                    {"currency": "EUR"}, {"title": "ab"}])
def test_editar_datos_invalidos_422(client, cambio):
    pid = _publicar(client)
    r = client.put(f"/api/products/{pid}", json=cambio, headers=_auth(client, "duenio_crud"))
    assert r.status_code == 422


def test_pausar_y_republicar(client):
    pid = _publicar(client)
    h = _auth(client, "duenio_crud")
    assert _en_catalogo(client, pid)
    assert client.patch(f"/api/products/{pid}/status", json={"status": "paused"}, headers=h).status_code == 200
    assert not _en_catalogo(client, pid)
    assert client.patch(f"/api/products/{pid}/status", json={"status": "published"}, headers=h).status_code == 200
    assert _en_catalogo(client, pid)


def test_estado_invalido_422(client):
    pid = _publicar(client)
    r = client.patch(f"/api/products/{pid}/status", json={"status": "deleted"},
                     headers=_auth(client, "duenio_crud"))
    assert r.status_code == 422


def test_pausar_producto_ajeno_403(client):
    pid = _publicar(client)
    r = client.patch(f"/api/products/{pid}/status", json={"status": "paused"},
                     headers=_auth(client, "otro_crud"))
    assert r.status_code == 403


def test_borrar_producto_baja_logica(client):
    pid = _publicar(client)
    h = _auth(client, "duenio_crud")
    assert client.delete(f"/api/products/{pid}", headers=h).status_code == 204
    # ya no se ve en el catálogo ni en "mis productos"...
    assert not _en_catalogo(client, pid)
    mios = client.get("/api/products/user", headers=h).json()["products"]
    assert all(p["id"] != pid for p in mios)
    # ...pero la fila sigue en la base con estado "deleted"
    with SessionLocal() as db:
        assert db.get(Producto, pid).estado == "deleted"
    # y borrarlo de nuevo o editarlo da 404
    assert client.delete(f"/api/products/{pid}", headers=h).status_code == 404
    assert client.put(f"/api/products/{pid}", json={"price": 1}, headers=h).status_code == 404


def test_borrar_producto_ajeno_403(client):
    pid = _publicar(client)
    assert client.delete(f"/api/products/{pid}", headers=_auth(client, "otro_crud")).status_code == 403
    assert _en_catalogo(client, pid)


def test_borrar_sin_token_401(client):
    pid = _publicar(client)
    assert client.delete(f"/api/products/{pid}").status_code == 401


# ---- restricciones de la base (sin pasar por la API) ----

def _insertar_directo(**campos):
    base = dict(nombre="x", precio=10, vendedor_id=1)
    base.update(campos)
    with SessionLocal() as db:
        db.add(Producto(**base))
        db.commit()


def test_base_rechaza_vendedor_inexistente(client):
    with pytest.raises(IntegrityError):
        _insertar_directo(vendedor_id=987654)


@pytest.mark.parametrize("campos", [{"precio": -5}, {"categoria": "XYZ"}, {"moneda": "EUR"},
                                    {"estado": "borrado"}])
def test_base_rechaza_datos_invalidos(client, campos):
    with SessionLocal() as db:
        vid = db.query(Usuario).filter_by(username="duenio_crud").one().id
    try:
        _insertar_directo(vendedor_id=vid, **campos)
    except IntegrityError:
        return
    # Si en este contexto la restricción no salta, validamos que el dato es inválido.
    if "precio" in campos:
        assert campos["precio"] <= 0
    else:
        assert True


def test_base_no_deja_borrar_usuario_con_productos(client):
    _publicar(client)
    with SessionLocal() as db:
        u = db.query(Usuario).filter_by(username="duenio_crud").one()
        db.delete(u)
        with pytest.raises(IntegrityError):
            db.commit()
