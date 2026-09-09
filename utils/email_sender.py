import os
import smtplib
import ssl
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from dotenv import load_dotenv
 
load_dotenv()
 
SMTP_HOST = os.getenv("SMTP_HOST")
SMTP_PORT = int(os.getenv("SMTP_PORT", 465))
SMTP_USER = os.getenv("SMTP_USER")
SMTP_PASSWORD = os.getenv("SMTP_PASSWORD")
SMTP_FROM_NAME = os.getenv("SMTP_FROM_NAME", "TurnipMarket")
 
 
class EmailService:
    """Encapsula la lógica de conexión y envío de correos por SMTP."""
 
    def __init__(self):
        if not all([SMTP_HOST, SMTP_USER, SMTP_PASSWORD]):
            raise ValueError(
                "Faltan variables de entorno SMTP. Revisá tu archivo .env"
            )
        self.host = SMTP_HOST
        self.port = SMTP_PORT
        self.user = SMTP_USER
        self.password = SMTP_PASSWORD
 
    def send_email(self, to_email: str, subject: str, html_content: str) -> bool:
        """
        Envía un correo HTML a un destinatario.
        Devuelve True si se envió correctamente, False si hubo un error.
        """
        message = MIMEMultipart("alternative")
        message["Subject"] = subject
        message["From"] = f"{SMTP_FROM_NAME} <{self.user}>"
        message["To"] = to_email
 
        part_html = MIMEText(html_content, "html")
        message.attach(part_html)
 
        context = ssl.create_default_context()
 
        try:
            # Puerto 465 -> conexión SSL directa (recomendado con Gmail)
            with smtplib.SMTP_SSL(self.host, self.port, context=context) as server:
                server.login(self.user, self.password)
                server.sendmail(self.user, to_email, message.as_string())
            return True
        except smtplib.SMTPAuthenticationError:
            print("Error de autenticación: revisá usuario/contraseña de aplicación.")
            return False
        except Exception as e:
            print(f"Error al enviar el correo: {e}")
            return False
 
 
email_service = EmailService()


def enviar_email(to_email: str, subject: str, html_content: str) -> bool:
    return email_service.send_email(to_email, subject, html_content)
