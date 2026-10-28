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
    crear_producto,
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

def _url_imagen(p: Producto, request: Request) -> str | None:
    if not p.imagen_url:
        return None
    if p.imagen_url.startswith(("http://", "https://")):
        return p.imagen_url
    return f"{str(request.base_url).rstrip('/')}{p.imagen_url}"


def _serializar(p: Producto, request: Request) -> dict:
    vendedor = p.vendedor
    return {
        "id": p.id,
        "title": p.nombre,
        "description": p.descripcion,
        "category": p.categoria,
        "price": float(p.precio),
        "currency": p.moneda,
        "condition": p.condicion,
        "image": _url_imagen(p, request),
        # Solo el alias público: nunca email ni teléfono del vendedor.
        "seller": (vendedor.alias or vendedor.username) if vendedor else None,
        "seller_id": p.vendedor_id,
        "status": p.estado,
        "created_at": p.fecha_creacion.isoformat() if p.fecha_creacion else None,
    }


@router.get("")
def get_productos(request: Request, db: Session = Depends(get_db)):
    return [_serializar(p, request) for p in listar_productos(db)]


@router.get("/user")
def get_mis_productos(
    request: Request,
    usuario: Usuario = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    productos = listar_productos_de_usuario(db, usuario.id)
    return {"products": [_serializar(p, request) for p in productos]}



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
    request: Request,
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
        "product": _serializar(producto, request),
    }