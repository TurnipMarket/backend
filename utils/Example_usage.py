import random
import string
 
from email_sender import EmailService
from templates import verification_code_template
 
 
def generate_otp(length: int = 6) -> str:
    """Genera un código numérico aleatorio (ej: '482913')."""
    return "".join(random.choices(string.digits, k=length))
 
 
def send_verification_email(to_email: str, username: str) -> str:
    """
    Genera un OTP, arma el HTML y lo envía.
    Devuelve el código generado para que lo guardes en la BD (con su expiración).
    """
    otp_code = generate_otp()
    html = verification_code_template(username, otp_code)
 
    success = EmailService.send_email(
        to_email=to_email,
        subject="Verificá tu cuenta - TurnipMarket",
        html_content=html,
    )
 
    if not success:
        raise RuntimeError("No se pudo enviar el correo de verificación")
 
    return otp_code
 
 
# --- Ejemplo de ejecución ---
if __name__ == "__main__":
    codigo = send_verification_email("soderiva918@gmail.com", "Martin Blanco")
    print(f"OTP generado y enviado: {codigo}")
    # En la app real, este 'codigo' se guarda en la BD junto a la hora de expiración,
    # NO se imprime en consola (esto es solo para probar localmente).
