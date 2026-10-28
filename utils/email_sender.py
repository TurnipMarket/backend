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


def _armar_mensaje(remitente: str, from_name: str, destino: str, asunto: str, html: str):
    mensaje = MIMEMultipart("alternative")
    mensaje["Subject"] = asunto
    mensaje["From"] = f"{from_name} <{remitente}>"
    mensaje["To"] = destino
    mensaje.attach(MIMEText(html, "html"))
    return mensaje


class EmailService:
    """Envía correos por SMTP. La configuración se lee del entorno al crearlo."""

    def __init__(self):
        self.cfg = _config()
        if not all(self.cfg[k] for k in ("host", "user", "password")):
            raise ValueError("Faltan variables de entorno SMTP. Revisá tu archivo .env")

    def send_email(self, to_email: str, subject: str, html_content: str) -> bool:
        """Devuelve True si se envió, False si hubo un error."""
        cfg = self.cfg
        mensaje = _armar_mensaje(cfg["user"], cfg["from_name"], to_email, subject, html_content)
        try:
            # Puerto 465 -> conexión SSL directa (recomendado con Gmail)
            with smtplib.SMTP_SSL(cfg["host"], cfg["port"], context=ssl.create_default_context()) as server:
                server.login(cfg["user"], cfg["password"])
                server.sendmail(cfg["user"], to_email, mensaje.as_string())
            return True
        except smtplib.SMTPAuthenticationError:
            logger.error("Error de autenticación SMTP: revisá usuario/contraseña de aplicación.")
        except Exception:
            logger.exception("Error al enviar el correo")
        return False


_email_service: EmailService | None = None


def _get_service() -> EmailService:
    """Crea el servicio recién al primer envío (no al importar el módulo)."""
    global _email_service
    if _email_service is None:
        _email_service = EmailService()
    return _email_service


def enviar_email(to_email: str, subject: str, html_content: str) -> bool:
    return _get_service().send_email(to_email, subject, html_content)