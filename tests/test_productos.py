"""POST /api/products: login con token, validaciones e imagen. Usa una base temporal."""
import base64
import os
import sys
import tempfile
from pathlib import Path

_tmp = tempfile.mkdtemp()
os.environ["DATABASE_PATH"] = str(Path(_tmp) / "test.db")
os.environ["UPLOAD_DIR"] = str(Path(_tmp) / "uploads")
os.environ["JWT_SECRET"] = "x" * 40
# El módulo de email exige SMTP al importarse; valores falsos, estos tests no envían mails.
for k in ("SMTP_HOST", "SMTP_USER", "SMTP_PASSWORD"):
    os.environ.setdefault(k, "test")
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import pytest
from fastapi.testclient import TestClient

from database.connection import SessionLocal
from main import app
from models.usuario import Usuario
from utils.security import hash_password

PNG = base64.b64encode(b"\x89PNG\r\n\x1a\n" + b"0" * 64).decode()
BODY = {
    "title": "Bici rodado 29",
    "description": "Bicicleta en buen estado, poco uso.",
    "category": "sports",
    "price": 45000,
    "currency": "ARS",
    "condition": "good",
}


@pytest.fixture(scope="module")
def client():
    with SessionLocal() as db:
        for nombre, verificado in (("vendedor", True), ("sinverificar", False)):
            db.add(Usuario(nombre=nombre, username=nombre, alias=nombre, email=f"{nombre}@t.com",
                           password=hash_password("Clave123!"), verificado=verificado))
        db.commit()
    return TestClient(app)


def _login(client, usuario):
    r = client.post("/api/auth/login", json={"identifier": usuario, "password": "Clave123!"})
    return r


def _auth(client):
    r = _login(client, "vendedor")
    assert r.status_code == 200
    assert r.json()["token"] and r.json()["expiresAt"] and r.json()["user"]["username"] == "vendedor"
    return {"Authorization": f"Bearer {r.json()['token']}"}


def test_sin_token_401(client):
    assert client.post("/api/products", json=BODY).status_code == 401


def test_token_falso_401(client):
    assert client.post("/api/products", json=BODY, headers={"Authorization": "Bearer abc"}).status_code == 401


def test_no_verificado_no_loguea(client):
    assert _login(client, "sinverificar").status_code == 403


def test_publicar_y_listar(client):
    h = _auth(client)
    r = client.post("/api/products", json={**BODY, "image": f"data:image/png;base64,{PNG}"}, headers=h)
    assert r.status_code == 201, r.text
    p = r.json()["product"]
    assert p["title"] == BODY["title"] and p["seller"] == "vendedor" and p["status"] == "published"
    assert p["image"].endswith(".png")
    assert client.get(p["image"]).status_code == 200  # se sirve desde /uploads

    cat = client.get("/api/products").json()
    assert any(x["id"] == p["id"] and x["seller"] == "vendedor" for x in cat)
    assert "email" not in str(cat)
    mine = client.get("/api/products/user", headers=h).json()["products"]
    assert [x["id"] for x in mine] == [p["id"]]


def test_sin_imagen_ok(client):
    assert client.post("/api/products", json=BODY, headers=_auth(client)).status_code == 201


@pytest.mark.parametrize("cambio", [
    {"title": "ab"}, {"description": "corta"}, {"price": 0}, {"price": -5},
    {"price": 1_000_000_000}, {"category": "armas"}, {"currency": "EUR"}, {"condition": "roto"},
])
def test_validaciones_422(client, cambio):
    assert client.post("/api/products", json={**BODY, **cambio}, headers=_auth(client)).status_code == 422


def test_imagen_invalida_400(client):
    h = _auth(client)
    falso = base64.b64encode(b"<script>alert(1)</script>").decode()
    assert client.post("/api/products", json={**BODY, "image": falso}, headers=h).status_code == 400
    assert client.post("/api/products", json={**BODY, "image": "%%%no-b64"}, headers=h).status_code == 400


def test_imagen_muy_grande_400(client):
    grande = base64.b64encode(b"\x89PNG\r\n\x1a\n" + b"0" * (5 * 1024 * 1024)).decode()
    assert client.post("/api/products", json={**BODY, "image": grande}, headers=_auth(client)).status_code == 400


def test_cors_preflight_red_local(client):
    r = client.options("/api/products", headers={
        "Origin": "http://192.168.220.145:5173",
        "Access-Control-Request-Method": "POST",
        "Access-Control-Request-Headers": "content-type,authorization",
    })
    assert r.status_code == 200
    assert client.options("/api/products", headers={
        "Origin": "http://evil.example.com", "Access-Control-Request-Method": "POST",
    }).status_code == 400
