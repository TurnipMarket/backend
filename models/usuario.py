import secrets
from datetime import datetime, timedelta, timezone
from sqlalchemy import Column, Integer, String, DateTime, Boolean
from database.connection import Base


def _utcnow():
    return datetime.now(timezone.utc).replace(tzinfo=None)


def generar_codigo() -> str:
    return str(secrets.randbelow(900000) + 100000)


class Usuario(Base):
    __tablename__ = "usuarios"

    id = Column(Integer, primary_key=True, index=True)
    nombre = Column(String(100), nullable=False)
    username = Column(String(50), unique=True, nullable=True, index=True)
    phone = Column(String(30), nullable=True)
    email = Column(String(255), unique=True, nullable=False, index=True)
    password = Column(String(255), nullable=False)
    fecha_creacion = Column(DateTime, default=_utcnow)
    verificado = Column(Boolean, default=False)
    codigo_verificacion = Column(String(6), nullable=True)
    codigo_expiracion = Column(DateTime, nullable=True)
    alias = Column(String(50), unique=True, nullable=True, index=True)

    def generar_nuevo_codigo(self, expiracion_minutos: int = 15) -> str:
        self.codigo_verificacion = generar_codigo()
        self.codigo_expiracion = _utcnow() + timedelta(minutes=expiracion_minutos)
        return self.codigo_verificacion

    def verificar_codigo(self, codigo: str) -> bool:
        if not self.codigo_verificacion or not self.codigo_expiracion:
            return False
        if _utcnow() > self.codigo_expiracion:
            return False
        return self.codigo_verificacion == codigo
