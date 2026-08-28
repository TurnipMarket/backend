from sqlalchemy.orm import Session, joinedload
from models.producto import Producto


def listar_productos(db: Session) -> list[Producto]:
    return (
        db.query(Producto)
        .options(joinedload(Producto.vendedor))
        .order_by(Producto.fecha_creacion.desc())
        .all()
    )