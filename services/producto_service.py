from decimal import Decimal

from sqlalchemy.orm import Session, joinedload
from models.producto import Producto
from models.usuario import Usuario


def listar_productos(db: Session) -> list[Producto]:
    return (
        db.query(Producto)
        .options(joinedload(Producto.vendedor))
        .filter(Producto.estado == "published")
        .order_by(Producto.fecha_creacion.desc())
        .all()
    )


def listar_productos_de_usuario(db: Session, usuario_id: int) -> list[Producto]:
    return (
        db.query(Producto)
        .options(joinedload(Producto.vendedor))
        .filter(Producto.vendedor_id == usuario_id)
        .order_by(Producto.fecha_creacion.desc())
        .all()
    )


def crear_producto(
    db: Session,
    vendedor: Usuario,
    titulo: str,
    descripcion: str,
    categoria: str,
    precio: Decimal,
    moneda: str,
    condicion: str,
    imagen_url: str | None,
) -> Producto:
    producto = Producto(
        nombre=titulo,
        descripcion=descripcion,
        categoria=categoria,
        precio=precio,
        moneda=moneda,
        condicion=condicion,
        imagen_url=imagen_url,
        estado="published",
        vendedor_id=vendedor.id,
    )
    db.add(producto)
    db.commit()
    db.refresh(producto)
    return producto
