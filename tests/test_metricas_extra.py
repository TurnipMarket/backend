import smtplib
import uuid
from unittest.mock import patch

import pytest
from fastapi.testclient import TestClient

from database.connection import SessionLocal
from main import app
from models.usuario import Usuario
from services.auth_service import (
    login_usuario,
    reenviar_codigo,
    registrar_usuario,
    verificar_disponibilidad,
    verificar_usuario,
)
from services.usuario_service import actualizar_alias, obtener_usuario_por_alias, obtener_usuario_por_id
from utils import templates
from utils.security import hash_password
import utils.email_sender as email_sender_mod


@pytest.fixture
def client():
    return TestClient(app)


def _uid():
    return uuid.uuid4().hex[:8]


def _nuevo_usuario(db, prefix, opciones=None):
    opciones = opciones or {}
    tag = f"{prefix}_{_uid()}"
    u = Usuario(
        nombre=tag,
        username=tag,
        alias=opciones.get("alias", tag),
        email=opciones.get("email", f"{tag}@test.com"),
        phone=opciones.get("phone"),
        password=hash_password(opciones.get("password", "Clave123!")),
        verificado=opciones.get("verificado", False),
    )
    db.add(u)
    db.commit()
    db.refresh(u)
    return u


def test_templates_render():
    c = templates.verification_code_template("ana", "123456", 15)
    assert "ana" in c and "123456" in c and "15" in c
    link = templates.verification_link_template("ana", "http://x/verify")
    assert "ana" in link and "http://x/verify" in link


def test_usuario_service_basico():
    with SessionLocal() as db:
        u = _nuevo_usuario(db, "svcusr")
        assert obtener_usuario_por_id(db, u.id).id == u.id
        assert obtener_usuario_por_alias(db, u.alias).id == u.id
        nuevo_alias = f"alias_{_uid()}"
        actualizado = actualizar_alias(db, u.id, nuevo_alias)
        assert actualizado.alias == nuevo_alias
        otro = _nuevo_usuario(db, "svcusr")
        with pytest.raises(ValueError):
            actualizar_alias(db, otro.id, nuevo_alias)
        with pytest.raises(ValueError):
            actualizar_alias(db, 99999999, f"x_{_uid()}")


def test_ruta_alias_usuario_inexistente(client):
    r = client.get(f"/api/usuarios/alias/nope_{_uid()}")
    assert r.status_code == 404


def test_registro_validaciones(client):
    tag = _uid()
    r = client.post("/api/auth/register", json={"username": "ab", "email": f"ab{tag}@t.com", "password": "Clave123!"})
    assert r.status_code in (400, 422)
    r = client.post("/api/auth/register", json={"username": "mal nombre!", "email": f"mn{tag}@t.com", "password": "Clave123!"})
    assert r.status_code in (400, 422)
    r = client.post("/api/auth/register", json={"username": f"mailbad{tag}", "email": "no-es-mail", "password": "Clave123!"})
    assert r.status_code in (400, 422)


def test_registro_duplicados(client):
    tag = _uid()
    with patch("services.auth_service.enviar_email", return_value=True):
        user1 = f"regok{tag}a"
        mail1 = f"{user1}@test.com"
        r = client.post("/api/auth/register", json={"username": user1, "email": mail1, "password": "Clave123!"})
        assert r.status_code == 201, r.text
        r2 = client.post("/api/auth/register", json={"username": f"regok{tag}b", "email": mail1, "password": "Clave123!"})
        assert r2.status_code == 400
        r3 = client.post("/api/auth/register", json={"username": user1, "email": f"regok{tag}c@test.com", "password": "Clave123!"})
        assert r3.status_code == 400


def _registrar_usuario_flow(client, username, email):
    with patch("services.auth_service.enviar_email", return_value=True):
        r = client.post("/api/auth/register", json={"username": username, "email": email, "password": "Clave123!"})
    assert r.status_code == 201, r.text
    data = r.json()
    uid = data.get("usuario_id") or data.get("user_id")
    if uid is None:
        with SessionLocal() as db:
            uid = db.query(Usuario).filter(Usuario.username == username).first().id
    return uid


def test_verificar_reenviar(client):
    tag = _uid()
    username = f"flowu{tag}"
    email = f"{username}@test.com"
    uid = _registrar_usuario_flow(client, username, email)
    assert client.post("/api/auth/login", json={"identifier": username, "password": "Clave123!"}).status_code == 403
    with patch("services.auth_service.enviar_email", return_value=True):
        assert client.post("/api/auth/resend-code", json={"email": email}).status_code == 200
    assert client.post("/api/auth/verify", json={"user_id": uid, "code": "000000"}).status_code == 400
    with SessionLocal() as db:
        code = db.query(Usuario).filter(Usuario.id == uid).first().codigo_verificacion
    assert client.post("/api/auth/verify", json={"user_id": uid, "code": code}).status_code == 200
    assert client.post("/api/auth/verify", json={"user_id": uid, "code": code}).status_code == 400


def test_login_disponibilidad(client):
    tag = _uid()
    username = f"flowd{tag}"
    email = f"{username}@test.com"
    uid = _registrar_usuario_flow(client, username, email)
    with SessionLocal() as db:
        u = db.query(Usuario).filter(Usuario.id == uid).first()
        u.verificado = True
        db.commit()
    r = client.post("/api/auth/login", json={"identifier": username, "password": "Clave123!"})
    assert r.status_code == 200
    data = r.json()
    got = data.get("username") or (data.get("user") or {}).get("username")
    assert got == username
    assert client.post("/api/auth/login", json={"identifier": username, "password": "Mala123!"}).status_code == 401
    assert client.get("/api/auth/availability", params={"field": "username", "value": username}).json().get("available") is False
    assert client.get("/api/auth/availability", params={"field": "email", "value": f"libre{tag}@test.com"}).json().get("available") is True
    assert client.get("/api/auth/availability", params={"field": "raro", "value": "x"}).status_code == 400


def test_servicios_auth_directo():
    with SessionLocal() as db:
        with pytest.raises(ValueError):
            verificar_usuario(db, 99999999, "1")
        with pytest.raises(ValueError):
            reenviar_codigo(db, f"nadie-{_uid()}@test.com")
        with pytest.raises(ValueError):
            verificar_disponibilidad(db, "otro", "x")
        assert verificar_disponibilidad(db, "username", f"UsuarioLibre{_uid()}") in (True, False)
        assert verificar_disponibilidad(db, "email", f"libre{_uid()}@test.com") in (True, False)


def _smtp_env(monkeypatch):
    monkeypatch.setenv("SMTP_HOST", "smtp.test")
    monkeypatch.setenv("SMTP_PORT", "465")
    monkeypatch.setenv("SMTP_USER", "u@test.com")
    monkeypatch.setenv("SMTP_PASSWORD", "pw")
    monkeypatch.setenv("SMTP_FROM_NAME", "TM")


def test_email_config_y_mensaje(monkeypatch):
    _smtp_env(monkeypatch)
    cfg = email_sender_mod._config()
    assert cfg["host"] == "smtp.test"
    msg = email_sender_mod._armar_mensaje("d@test.com", "Sub", "<b>x</b>", {"email": "u@test.com", "name": "TM"})
    assert msg["To"] == "d@test.com" and msg["Subject"] == "Sub"


def test_email_service_envios(monkeypatch):
    _smtp_env(monkeypatch)
    RealEmailService = email_sender_mod.EmailService

    class DummySMTP:
        def __init__(self, *a, **k): pass
        def __enter__(self): return self
        def __exit__(self, *a): return False
        def login(self, *a, **k): return True
        def sendmail(self, *a, **k): return {}

    monkeypatch.setattr(smtplib, "SMTP_SSL", DummySMTP)
    svc = RealEmailService()
    assert svc.send_email("d@test.com", "s", "<p>h</p>") is True

    class AuthFail(DummySMTP):
        def login(self, *a, **k): raise smtplib.SMTPAuthenticationError(1, b"no")
    monkeypatch.setattr(smtplib, "SMTP_SSL", AuthFail)
    assert svc.send_email("d@test.com", "s", "h") is False

    class Boom(DummySMTP):
        def sendmail(self, *a, **k): raise RuntimeError("boom")
    monkeypatch.setattr(smtplib, "SMTP_SSL", Boom)
    assert svc.send_email("d@test.com", "s", "h") is False


def test_email_service_cache_y_errores(monkeypatch):
    _smtp_env(monkeypatch)
    RealEmailService = email_sender_mod.EmailService
    old_service = email_sender_mod._email_service
    try:
        email_sender_mod._email_service = None
        monkeypatch.setattr(email_sender_mod, "EmailService", lambda: type("S", (), {"send_email": lambda *a, **k: True})())
        assert email_sender_mod.enviar_email("d@test.com", "s", "h") is True
        monkeypatch.setattr(email_sender_mod, "EmailService", RealEmailService)
        email_sender_mod._email_service = None
        monkeypatch.delenv("SMTP_HOST", raising=False)
        with pytest.raises(ValueError):
            RealEmailService()
    finally:
        email_sender_mod._email_service = old_service
