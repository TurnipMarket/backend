from datetime import datetime, timezone
from sqlalchemy import CheckConstraint, Column, Integer, String, Numeric, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from database.connection import Base


def _utcnow():
    return datetime.now(timezone.utc).replace(tzinfo=None)


class Producto(Base):
    __tablename__ = "productos"
    # Restricciones en la base (valen para bases nuevas): aunque alguien se saltee la API,
    # la base rechaza precios negativos y valores fuera de las listas permitidas.
    __table_args__ = (
        CheckConstraint("precio > 0", name="ck_productos_precio"),
        CheckConstraint("moneda IN ('ARS','USD','UYU')", name="ck_productos_moneda"),
        CheckConstraint(
            "categoria IN ('electronics','clothing','home','sports','books','vehicles','services','other')",
            name="ck_productos_categoria",
        ),
        CheckConstraint("condicion IN ('new','like_new','good','fair')", name="ck_productos_condicion"),
        CheckConstraint("estado IN ('published','paused','deleted')", name="ck_productos_estado"),
    )

    id = Column(Integer, primary_key=True, index=True)
    nombre = Column(String(150), nullable=False)
    descripcion = Column(String(2000), nullable=True)
    precio = Column(Numeric(12, 2), nullable=False)
    imagen_url = Column(String(500), nullable=True)
    categoria = Column(String(30), nullable=False, default="other", server_default="other")
    moneda = Column(String(3), nullable=False, default="ARS", server_default="ARS")
    condicion = Column(String(20), nullable=False, default="new", server_default="new")
    estado = Column(String(20), nullable=False, default="published", server_default="published")
    vendedor_id = Column(Integer, ForeignKey("usuarios.id", ondelete="RESTRICT"), nullable=False, index=True)
    fecha_creacion = Column(DateTime, default=_utcnow)

    vendedor = relationship("Usuario")
