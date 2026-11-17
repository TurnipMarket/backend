from decimal import Decimal

from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel, ConfigDict, Field
from sqlalchemy.orm import Session

from database.connection import get_db
from models.producto import Producto
from models.usuario import Usuario
from services.imagen_service import borrar_imagen, guardar_imagen
from services.producto_service import (
    NuevoProducto,
    actualizar_producto,
    crear_producto,
    dar_de_baja_producto,
    listar_productos,
    listar_productos_de_usuario,
)
from utils.dependencies import get_current_user

router = APIRouter(prefix="/api/products", tags=["products"])

CATEGORIAS = r"^(electronics|clothing|home|sports|books|vehicles|services|other)$"
MONEDAS = r"^(ARS|USD|UYU)$"
CONDICIONES = r"^(new|like_new|good|fair)$"


class ProductoCreate(BaseModel):
    """Mismos nombres y límites que el formulario del frontend (CreateProductPage)."""

    model_config = {"str_strip_whitespace": True}

    title: str = Field(min_length=3, max_length=100)
    description: str = Field(min_length=10, max_length=2000)
    category: str = Field(default="other", pattern=CATEGORIAS)
    price: Decimal = Field(gt=0, le=999_999_999, max_digits=12, decimal_places=2)
    currency: str = Field(default="ARS", pattern=MONEDAS)
    condition: str = Field(default="new", pattern=CONDICIONES)
    # data URL o base64 de la foto (máx 5MB reales ≈ 7,0M de caracteres en base64).
    image: str | None = Field(default=None, max_length=7_200_000)

class ProductoUpdate(BaseModel):
    """Edición parcial: se manda solo lo que cambia. Mismos límites que ProductoCreate."""

    model_config = {"str_strip_whitespace": True}

    title: str | None = Field(default=None, min_length=3, max_length=100)
    description: str | None = Field(default=None, min_length=10, max_length=2000)
    category: str | None = Field(default=None, pattern=CATEGORIAS)
    price: Decimal | None = Field(default=None, gt=0, le=999_999_999, max_digits=12, decimal_places=2)
    currency: str | None = Field(default=None, pattern=MONEDAS)
    condition: str | None = Field(default=None, pattern=CONDICIONES)


class EstadoUpdate(BaseModel):
    # Desde acá solo se publica o se pausa; para dar de baja se usa DELETE.
    status: str = Field(pattern=r"^(published|paused)$")


# Nombre que usa la API (frontend) -> nombre de la columna en la base.
_CAMPO_A_COLUMNA = {
    "title": "nombre",
    "description": "descripcion",
    "category": "categoria",
    "price": "precio",
    "currency": "moneda",
    "condition": "condicion",
}


def _url_imagen(p: Producto) -> str | None:
    if not p.imagen_url:
        return None
    if p.imagen_url.startswith(("http://", "https://")):
        return p.imagen_url
    if p.imagen_url.startswith("/"):
        return p.imagen_url
    return f"/{p.imagen_url}"


def _serializar(p: Producto) -> dict:
    vendedor = p.vendedor
    return {
        "id": p.id,
        "title": p.nombre,
        "description": p.descripcion,
        "category": p.categoria,
        "price": float(p.precio),
        "currency": p.moneda,
        "condition": p.condicion,
        "image": _url_imagen(p),
        # Solo el alias público: nunca email ni teléfono del vendedor.
        "seller": (vendedor.alias or vendedor.username) if vendedor else None,
        "seller_id": p.vendedor_id,
        "status": p.estado,
        "created_at": p.fecha_creacion.isoformat() if p.fecha_creacion else None,
    }


@router.get("")
def get_productos(db: Session = Depends(get_db)):
    return [_serializar(p) for p in listar_productos(db)]


@router.get("/user")
def get_mis_productos(
    usuario: Usuario = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    productos = listar_productos_de_usuario(db, usuario.id)
    return {"products": [_serializar(p) for p in productos]}



def _guardar_imagen_o_400(imagen: str | None) -> str | None:
    if not imagen:
        return None
    try:
        return guardar_imagen(imagen)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


def _a_nuevo_producto(req: ProductoCreate, imagen_url: str | None) -> NuevoProducto:
    return NuevoProducto(
        titulo=req.title,
        descripcion=req.description,
        categoria=req.category,
        precio=req.price,
        moneda=req.currency,
        condicion=req.condition,
        imagen_url=imagen_url,
    )


@router.post("", status_code=201)
def post_producto(
    req: ProductoCreate,
    usuario: Usuario = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    imagen_url = _guardar_imagen_o_400(req.image)
    try:
        producto = crear_producto(db, usuario, _a_nuevo_producto(req, imagen_url))
    except Exception:
        db.rollback()
        borrar_imagen(imagen_url)
        raise

    return {
        "message": "Producto publicado correctamente.",
        "product": _serializar(producto),
    }


def _error_http(e: Exception) -> HTTPException:
    if isinstance(e, LookupError):
        return HTTPException(status_code=404, detail=str(e))
    return HTTPException(status_code=403, detail=str(e))


@router.put("/{producto_id}")
def put_producto(
    producto_id: int,
    req: ProductoUpdate,
    usuario: Usuario = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """UPDATE: editar mi publicación (título, descripción, categoría, precio, moneda, condición)."""
    cambios = {
        _CAMPO_A_COLUMNA[campo]: valor
        for campo, valor in req.model_dump(exclude_unset=True).items()
        if valor is not None
    }
    if not cambios:
        raise HTTPException(status_code=400, detail="No hay cambios para guardar")
    try:
        producto = actualizar_producto(db, usuario, producto_id, cambios)
    except (LookupError, PermissionError) as e:
        raise _error_http(e)
    return {
        "message": "Producto actualizado correctamente.",
        "product": _serializar(producto),
    }


@router.patch("/{producto_id}/status")
def patch_estado_producto(
    producto_id: int,
    req: EstadoUpdate,
    usuario: Usuario = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """UPDATE: pausar o volver a publicar mi publicación."""
    try:
        producto = actualizar_producto(db, usuario, producto_id, {"estado": req.status})
    except (LookupError, PermissionError) as e:
        raise _error_http(e)
    return {
        "message": "Estado actualizado correctamente.",
        "product": _serializar(producto),
    }


@router.delete("/{producto_id}", status_code=204)
def delete_producto(
    producto_id: int,
    usuario: Usuario = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """DELETE (baja lógica): la publicación deja de verse pero la fila queda en la base."""
    try:
        imagen = dar_de_baja_producto(db, usuario, producto_id)
    except (LookupError, PermissionError) as e:
        raise _error_http(e)
    borrar_imagen(imagen)
