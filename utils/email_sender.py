import logging
import os
import smtplib
import ssl
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

from dotenv import load_dotenv

load_dotenv()

logger = logging.getLogger(__name__)


def _config() -> dict:
    return {
        "host": os.getenv("SMTP_HOST"),
        "port": int(os.getenv("SMTP_PORT", 465)),
        "user": os.getenv("SMTP_USER"),
        "password": os.getenv("SMTP_PASSWORD"),
        "from_name": os.getenv("SMTP_FROM_NAME", "TurnipMarket"),
    }


def _armar_mensaje(destino: str, asunto: str, contenido: str, remitente: dict):
    mensaje = MIMEMultipart("alternative")
    mensaje["Subject"] = asunto
    mensaje["From"] = f"{remitente.get('name', 'TurnipMarket')} <{remitente['email']}>"
    mensaje["To"] = destino
    mensaje.attach(MIMEText(contenido, "html"))
    return mensaje


def _enviar_smtp(cfg: dict, destino: str, mensaje) -> bool:
    """devuelve True si se envió, False si hubo un error de conexión o de login."""
    try:
        # puerto 465: conexión ssl directa (recomendado con gmail)
        with smtplib.SMTP_SSL(cfg["host"], cfg["port"], context=ssl.create_default_context()) as server:
            server.login(cfg["user"], cfg["password"])
            server.sendmail(cfg["user"], destino, mensaje.as_string())
        return True
    except smtplib.SMTPAuthenticationError:
        logger.error("autenticación smtp fallida: revisá usuario y contraseña de aplicación")
    except Exception:
        logger.exception("error al enviar el correo")
    return False


class EmailService:
    """envía correos por smtp. la configuración se lee del entorno al crearlo."""

    def __init__(self):
        self.cfg = _config()
        if not all(self.cfg[k] for k in ("host", "user", "password")):
            raise ValueError("faltan variables de entorno de correo, revisá tu archivo .env")

    def send_email(self, to_email: str, subject: str, html_content: str) -> bool:
        cfg = self.cfg
        remitente = {"email": cfg["user"], "name": cfg["from_name"]}
        mensaje = _armar_mensaje(to_email, subject, html_content, remitente)
        return _enviar_smtp(cfg, to_email, mensaje)


_email_service: EmailService | None = None


def _get_service() -> EmailService:
    """Crea el servicio recién al primer envío (no al importar el módulo)."""
    global _email_service
    if _email_service is None:
        _email_service = EmailService()
    return _email_service


def enviar_email(to_email: str, subject: str, html_content: str) -> bool:
    return _get_service().send_email(to_email, subject, html_content)