from datetime import datetime, timezone
from sqlalchemy import Column, Integer, String, Numeric, DateTime, ForeignKey, Text
from sqlalchemy.orm import relationship
from database.connection import Base


def _utcnow():
    return datetime.now(timezone.utc).replace(tzinfo=None)


class Producto(Base):
    __tablename__ = "productos"

    id = Column(Integer, primary_key=True, index=True)
    nombre = Column(String(150), nullable=False)
    descripcion = Column(Text, nullable=True)
    precio = Column(Numeric(12, 2), nullable=False)
    imagen_url = Column(String(500), nullable=True)
    categoria = Column(String(30), nullable=False, default="other", server_default="other")
    moneda = Column(String(3), nullable=False, default="ARS", server_default="ARS")
    condicion = Column(String(20), nullable=False, default="new", server_default="new")
    estado = Column(String(20), nullable=False, default="published", server_default="published")
    vendedor_id = Column(Integer, ForeignKey("usuarios.id"), nullable=False)
    fecha_creacion = Column(DateTime, default=_utcnow)

    vendedor = relationship("Usuario")
