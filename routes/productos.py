from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from database.connection import get_db
from services.producto_service import listar_productos

router = APIRouter(prefix="/api/products", tags=["products"])


@router.get("")
def get_productos(db: Session = Depends(get_db)):
    productos = listar_productos(db)
    return [
        {
            "id": p.id,
            "nombre": p.nombre,
            "descripcion": p.descripcion,
            "precio": float(p.precio),
            "imagen": p.imagen_url,
            "vendedor": {
                "id": p.vendedor.id,
                "nombre": p.vendedor.nombre,
                "alias": p.vendedor.alias,
            } if p.vendedor else None,
        }
        for p in productos
    ]