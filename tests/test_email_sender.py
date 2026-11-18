"""EmailService con SMTP simulado: no se envía ningún correo real."""
import smtplib
from unittest.mock import MagicMock, patch

import pytest

from utils import email_sender
from utils.email_sender import EmailService

SMTP_FALSO = {"SMTP_HOST": "smtp.test", "SMTP_USER": "user@test.com", "SMTP_PASSWORD": "clave"}


@pytest.fixture
def servicio(monkeypatch):
    for clave, valor in SMTP_FALSO.items():
        monkeypatch.setenv(clave, valor)
    return EmailService()


def _enviar(servicio):
    return servicio.send_email(to_email="destino@test.com", subject="Test", html_content="<p>Hola</p>")


@patch("utils.email_sender.smtplib.SMTP_SSL")
def test_send_email_ok(mock_smtp_ssl, servicio):
    server = MagicMock()
    mock_smtp_ssl.return_value.__enter__.return_value = server

    assert _enviar(servicio) is True
    server.login.assert_called_once()
    server.sendmail.assert_called_once()


@patch("utils.email_sender.smtplib.SMTP_SSL")
def test_send_email_error_de_autenticacion(mock_smtp_ssl, servicio):
    server = MagicMock()
    server.login.side_effect = smtplib.SMTPAuthenticationError(535, b"bad credentials")
    mock_smtp_ssl.return_value.__enter__.return_value = server

    assert _enviar(servicio) is False


@patch("utils.email_sender.smtplib.SMTP_SSL", side_effect=OSError("sin red"))
def test_send_email_error_generico(_mock_smtp_ssl, servicio):
    assert _enviar(servicio) is False


def test_sin_variables_smtp_falla(monkeypatch):
    for clave in SMTP_FALSO:
        monkeypatch.delenv(clave, raising=False)
    with pytest.raises(ValueError):
        EmailService()


def test_enviar_email_delega_en_el_servicio():
    falso = MagicMock()
    falso.send_email.return_value = True
    with patch.object(email_sender, "_get_service", return_value=falso):
        assert email_sender.enviar_email("a@b.com", "Asunto", "<p>x</p>") is True
    falso.send_email.assert_called_once_with("a@b.com", "Asunto", "<p>x</p>")