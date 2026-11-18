"""Registro, verificación, reenvío y login (el envío de mails está simulado)."""
import pytest
from fastapi.testclient import TestClient
 
from database.connection import SessionLocal
from main import app
from models.usuario import Usuario
 
CLAVE = "Clave123!"
 
 
@pytest.fixture(autouse=True)
def sin_mails(monkeypatch):
    enviados = []
    monkeypatch.setattr(
        "services.auth_service.enviar_email",
        lambda to, asunto, cuerpo: enviados.append((to, cuerpo)) or True,
    )
    return enviados
 
 
@pytest.fixture(scope="module")
def client():
    return TestClient(app)
 
 
def _registrar(client, username, email):
    return client.post("/api/auth/register", json={"username": username, "email": email, "password": CLAVE})
 
 
def _codigo(usuario_id):
    with SessionLocal() as db:
        return db.get(Usuario, usuario_id).codigo_verificacion
 
 
def test_registro_ok_y_envia_codigo(client, sin_mails):
    r = _registrar(client, "auth_ana", "auth_ana@t.com")
    assert r.status_code == 201, r.text
    assert r.json()["verificado"] is False
    assert sin_mails and sin_mails[0][0] == "auth_ana@t.com"
 
 
def test_registro_username_repetido_400(client):
    assert _registrar(client, "auth_rep", "auth_rep1@t.com").status_code == 201
    r = _registrar(client, "auth_rep", "auth_rep2@t.com")
    assert r.status_code == 400
    assert "en uso" in r.json()["detail"]
 
 
def test_registro_email_repetido_400(client):
    assert _registrar(client, "auth_em1", "auth_dup@t.com").status_code == 201
    r = _registrar(client, "auth_em2", "auth_dup@t.com")
    assert r.status_code == 400
    assert "email" in r.json()["detail"].lower()
 
 
def test_dos_registros_sin_email_no_chocan(client):
    for nombre in ("auth_tel1", "auth_tel2"):
        r = client.post("/api/auth/register", json={"username": nombre, "phone": "123", "password": CLAVE})
        assert r.status_code == 201, r.text
 
 
@pytest.mark.parametrize("username,email", [("ab", "ok@t.com"), ("con espacio!", "ok2@t.com"), ("auth_mal", "no-es-mail")])
def test_registro_datos_invalidos_400(client, username, email):
    assert _registrar(client, username, email).status_code == 400
 
 
def test_login_sin_verificar_403_y_verificado_200(client):
    uid = _registrar(client, "auth_flow", "auth_flow@t.com").json()["usuario_id"]
    login = {"identifier": "auth_flow", "password": CLAVE}
    assert client.post("/api/auth/login", json=login).status_code == 403
 
    r = client.post("/api/auth/verify", json={"user_id": uid, "code": _codigo(uid)})
    assert r.status_code == 200
    ok = client.post("/api/auth/login", json=login)
    assert ok.status_code == 200 and ok.json()["token"]
 
 
def test_verificar_codigo_incorrecto_400(client):
    uid = _registrar(client, "auth_bad", "auth_bad@t.com").json()["usuario_id"]
    r = client.post("/api/auth/verify", json={"user_id": uid, "code": "000000"})
    assert r.status_code == 400
 
 
def test_login_clave_incorrecta_401(client):
    _registrar(client, "auth_pwd", "auth_pwd@t.com")
    r = client.post("/api/auth/login", json={"identifier": "auth_pwd", "password": "otra"})
    assert r.status_code == 401
 
 
def test_reenviar_codigo(client, sin_mails):
    _registrar(client, "auth_res", "auth_res@t.com")
    sin_mails.clear()
    assert client.post("/api/auth/resend-code", json={"email": "auth_res@t.com"}).status_code == 200
    assert len(sin_mails) == 1
    assert client.post("/api/auth/resend-code", json={"email": "nadie@t.com"}).status_code == 400
 
 
def test_disponibilidad(client):
    _registrar(client, "auth_disp", "auth_disp@t.com")
    r = client.get("/api/auth/availability", params={"field": "username", "value": "auth_disp"})
    assert r.json() == {"available": False}
    r = client.get("/api/auth/availability", params={"field": "email", "value": "libre@t.com"})
    assert r.json() == {"available": True}
    assert client.get("/api/auth/availability", params={"field": "otro", "value": "x"}).status_code == 400