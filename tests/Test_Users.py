"""Endpoints /api/usuarios: lectura por id/alias y cambio de alias."""
import pytest
from fastapi.testclient import TestClient

from database.connection import SessionLocal
from main import app
from models.usuario import Usuario
from utils.security import hash_password


@pytest.fixture(scope="module")
def client():
    with SessionLocal() as db:
        for nombre in ("usr_uno", "usr_dos"):
            db.add(Usuario(nombre=nombre, username=nombre, alias=nombre, email=f"{nombre}@t.com",
                           password=hash_password("Clave123!"), verificado=True))
        db.commit()
    return TestClient(app)


def _id(username):
    with SessionLocal() as db:
        return db.query(Usuario).filter(Usuario.username == username).one().id


def test_get_usuario_por_id(client):
    r = client.get(f"/api/usuarios/{_id('usr_uno')}")
    assert r.status_code == 200
    assert r.json()["alias"] == "usr_uno"


def test_get_usuario_inexistente_404(client):
    assert client.get("/api/usuarios/999999").status_code == 404


def test_get_usuario_por_alias(client):
    r = client.get("/api/usuarios/alias/usr_dos")
    assert r.status_code == 200
    assert "email" not in r.json()
    assert client.get("/api/usuarios/alias/no_existe").status_code == 404


def test_cambiar_alias_ok(client):
    uid = _id("usr_uno")
    r = client.put(f"/api/usuarios/{uid}/alias", json={"alias": "usr_uno_nuevo"})
    assert r.status_code == 200
    assert r.json()["alias"] == "usr_uno_nuevo"


def test_cambiar_alias_en_uso_400(client):
    r = client.put(f"/api/usuarios/{_id('usr_dos')}/alias", json={"alias": "usr_uno_nuevo"})
    assert r.status_code == 400


def test_cambiar_alias_usuario_inexistente_400(client):
    assert client.put("/api/usuarios/999999/alias", json={"alias": "cualquiera"}).status_code == 400