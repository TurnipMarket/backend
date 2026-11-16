from dataclasses import dataclass
from decimal import Decimal
from sqlalchemy.orm import Session, joinedload
from models.producto import Producto
from models.usuario import Usuario
from pydantic import BaseModel, Field


def listar_productos(db: Session) -> list[Producto]:
    return (
        db.query(Producto)
        .options(joinedload(Producto.vendedor))
        .filter(Producto.estado == "published")
        .order_by(Producto.fecha_creacion.desc())
        .all()
    )


def listar_productos_de_usuario(db: Session, usuario_id: int) -> list[Producto]:
    # Los productos dados de baja ("deleted") no aparecen en "Mis publicaciones".
    return (
        db.query(Producto)
        .options(joinedload(Producto.vendedor))
        .filter(Producto.vendedor_id == usuario_id, Producto.estado != "deleted")
        .order_by(Producto.fecha_creacion.desc())
        .all()
    )


@dataclass
class NuevoProducto:
    titulo: str
    descripcion: str
    categoria: str
    precio: Decimal
    moneda: str
    condicion: str
    imagen_url: str | None = None


def crear_producto(db: Session, vendedor: Usuario, datos: NuevoProducto) -> Producto:
    producto = Producto(
        nombre=datos.titulo,
        descripcion=datos.descripcion,
        categoria=datos.categoria,
        precio=datos.precio,
        moneda=datos.moneda,
        condicion=datos.condicion,
        imagen_url=datos.imagen_url,
        estado="published",
        vendedor_id=vendedor.id,
    )
    db.add(producto)
    db.commit()
    db.refresh(producto)
    return producto


# ---------------------------------------------------------------------------
# UPDATE y DELETE (RF07): solo el dueño de la publicación puede tocarla.
# Los errores son LookupError (no existe) y PermissionError (no es tuya);
# la ruta los convierte en 404 y 403.
# ---------------------------------------------------------------------------

# Campos del modelo que se pueden modificar desde la API.
CAMPOS_EDITABLES = {"nombre", "descripcion", "categoria", "precio", "moneda", "condicion", "estado"}


def _producto_del_vendedor(db: Session, producto_id: int, usuario: Usuario) -> Producto:
    producto = db.get(Producto, producto_id)
    if producto is None or producto.estado == "deleted":
        raise LookupError("Producto no encontrado")
    if producto.vendedor_id != usuario.id:
        raise PermissionError("Esta publicación no es tuya")
    return producto


def actualizar_producto(
    db: Session, usuario: Usuario, producto_id: int, cambios: dict
) -> Producto:
    """UPDATE: modifica solo los campos recibidos (nombres del modelo, ej. 'precio')."""
    producto = _producto_del_vendedor(db, producto_id, usuario)
    for campo, valor in cambios.items():
        if campo in CAMPOS_EDITABLES:
            setattr(producto, campo, valor)
    db.commit()
    db.refresh(producto)
    return producto


def dar_de_baja_producto(db: Session, usuario: Usuario, producto_id: int) -> str | None:
    """DELETE lógico: estado = 'deleted'. No se borra la fila, así se conserva el historial.

    Devuelve la imagen que tenía, para que la ruta la borre del disco.
    """
    producto = _producto_del_vendedor(db, producto_id, usuario)
    imagen = producto.imagen_url
    producto.estado = "deleted"
    producto.imagen_url = None
    db.commit()
    return imagen
