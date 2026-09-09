def verification_code_template(username: str, otp_code: str, expiration_minutes: int = 10) -> str:
    """Plantilla para enviar un código OTP de 6 dígitos."""
    return f"""
    <html>
      <body style="font-family: Arial, sans-serif; background-color: #f4f4f4; padding: 20px;">
        <div style="max-width: 500px; margin: auto; background: white; border-radius: 8px; padding: 30px; text-align: center;">
          <h2 style="color: #2e7d32;">TurnipMarket</h2>
          <p>Hola <strong>{username}</strong>, tu código de verificación es:</p>
          <div style="font-size: 32px; font-weight: bold; letter-spacing: 6px; color: #2e7d32; margin: 20px 0;">
            {otp_code}
          </div>
          <p>Este código expira en {expiration_minutes} minutos.</p>
          <p style="font-size: 12px; color: #999;">Si no solicitaste esto, ignorá este correo.</p>
        </div>
      </body>
    </html>
    """
 
 
def verification_link_template(username: str, verification_link: str) -> str:
    """Plantilla alternativa: enlace de verificación en vez de código."""
    return f"""
    <html>
      <body style="font-family: Arial, sans-serif; background-color: #f4f4f4; padding: 20px;">
        <div style="max-width: 500px; margin: auto; background: white; border-radius: 8px; padding: 30px; text-align: center;">
          <h2 style="color: #2e7d32;">TurnipMarket</h2>
          <p>Hola <strong>{username}</strong>, hacé clic en el botón para verificar tu cuenta:</p>
          <a href="{verification_link}"
             style="display:inline-block; padding: 12px 24px; background-color:#2e7d32; color:white; text-decoration:none; border-radius:5px; margin-top:15px;">
             Verificar mi cuenta
          </a>
          <p style="font-size: 12px; color: #999; margin-top: 20px;">
            Si el botón no funciona, copiá y pegá este enlace: {verification_link}
          </p>
        </div>
      </body>
    </html>
    """
