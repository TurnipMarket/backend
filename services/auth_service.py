import re
import random
from dataclasses import dataclass
from sqlalchemy import or_
from sqlalchemy.orm import Session
from models.usuario import Usuario
from utils.security import hash_password, verify_password
from utils.email_sender import enviar_email

CAMPOS_DISPONIBLES = {"username", "email"}
@dataclass
class DatosRegistro:
    username: str
    password: str
    email: str | None = None
    phone: str | None = None


def _normalizar_username(username: str) -> str:
    return username.strip().lower().replace(" ", "")


def _validar_username(username: str) -> None:
    if len(username) < 3:
        raise ValueError("El nombre de usuario debe tener al menos 3 caracteres")
    if not re.match(r"^[a-zA-Z0-9_.-]+$", username):
        raise ValueError("El nombre de usuario solo puede contener letras, números, puntos, guiones y guion bajo")


def _validar_email(email: str) -> None:
    if not re.match(r"^[^@\s]+@[^@\s]+\.[^@\s]+$", email):
        raise ValueError("El email no es válido")


def _generar_alias(db: Session, base: str) -> str:
    alias = base.lower()[:20]
    while db.query(Usuario).filter(Usuario.alias == alias).first():
        alias = f"{base.lower()[:20]}{random.randint(10, 99)}"
    return alias


def _normalizar_datos(datos: DatosRegistro) -> tuple[str, str | None]:
    username = _normalizar_username(datos.username)
    _validar_username(username)
    email = datos.email.strip().lower() if datos.email else None
    if email:
        _validar_email(email)
    return username, email


def _validar_unicidad(db: Session, username: str, email: str | None) -> None:
    if email and db.query(Usuario).filter(Usuario.email == email).first():
        raise ValueError("El email ya está registrado")
    if db.query(Usuario).filter(Usuario.username == username).first():
        raise ValueError("El nombre de usuario ya está en uso")


def _crear_usuario(db: Session, datos: DatosRegistro, username: str, email: str | None) -> Usuario:
    usuario = Usuario(
        nombre=username,
        username=username,
        phone=datos.phone,
        email=email,
        password=hash_password(datos.password),
        verificado=False,
        alias=_generar_alias(db, username),
    )
    db.add(usuario)
    db.commit()
    db.refresh(usuario)
    return usuario


def registrar_usuario(db: Session, datos: DatosRegistro) -> Usuario:
    username, email = _normalizar_datos(datos)
    _validar_unicidad(db, username, email)
    usuario = _crear_usuario(db, datos, username, email)

    codigo = usuario.generar_nuevo_codigo()
    db.commit()
    _enviar_codigo(email, codigo)
    return usuario

def _enviar_codigo(email: str, codigo: str) -> None:
    asunto = "Código de verificación - TurnipMarket"
    cuerpo = f"Tu código de verificación es: {codigo}\n\nVálido por 15 minutos."
    try:
        enviar_email(email, asunto, cuerpo)
    except Exception as e:
        raise ValueError(f"Error al enviar el email: {e}")


def verificar_usuario(db: Session, user_id: int, codigo: str) -> Usuario:
    usuario = db.query(Usuario).filter(Usuario.id == user_id).first()
    if not usuario:
        raise ValueError("Usuario no encontrado")
    if usuario.verificado:
        raise ValueError("El usuario ya está verificado")
    if not usuario.verificar_codigo(codigo):
        raise ValueError("Código inválido o expirado")

    usuario.verificado = True
    usuario.codigo_verificacion = None
    usuario.codigo_expiracion = None
    db.commit()
    return usuario


def reenviar_codigo(db: Session, email: str) -> Usuario:
    usuario = db.query(Usuario).filter(Usuario.email == email).first()
    if not usuario:
        raise ValueError("Email no encontrado")
    if usuario.verificado:
        raise ValueError("El usuario ya está verificado")

    codigo = usuario.generar_nuevo_codigo()
    db.commit()
    _enviar_codigo(email, codigo)
    return usuario


def login_usuario(db: Session, identifier: str, password: str) -> dict | None:
    identifier = identifier.strip().lower()
    usuario = (
        db.query(Usuario)
        .filter(
            or_(
                Usuario.email == identifier,
                Usuario.username == identifier,
                Usuario.alias == identifier,
            )
        )
        .first()
    )
    if not usuario:
        return None
    if not verify_password(usuario.password, password):
        return None
    if usuario.verificado is False:
        raise ValueError("Debes verificar tu email antes de iniciar sesión")
    return {
        "usuario_id": usuario.id,
        "nombre": usuario.nombre,
        "username": usuario.username,
        "alias": usuario.alias,
        "email": usuario.email,
        "phone": usuario.phone,
    }


def verificar_disponibilidad(db: Session, campo: str, valor: str) -> bool:
    if campo not in CAMPOS_DISPONIBLES:
        raise ValueError(f"Campo '{campo}' no es válido")
    valor = valor.strip().lower()
    if campo == "username":
        valor = _normalizar_username(valor)
        existe = db.query(Usuario).filter(Usuario.username == valor).first()
    else:
        existe = db.query(Usuario).filter(Usuario.email == valor).first()
    return existe is None