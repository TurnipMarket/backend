from sqlalchemy.orm import Session
from models.usuario import Usuario


def obtener_usuario_por_id(db: Session, usuario_id: int) -> Usuario | None:
    return db.query(Usuario).filter(Usuario.id == usuario_id).first()


def obtener_usuario_por_alias(db: Session, alias: str) -> Usuario | None:
    return db.query(Usuario).filter(Usuario.alias == alias).first()


def actualizar_alias(db: Session, usuario_id: int, nuevo_alias: str) -> Usuario:
    existente = db.query(Usuario).filter(Usuario.alias == nuevo_alias).first()
    if existente and existente.id != usuario_id:
        raise ValueError("El alias ya está en uso")

    usuario = obtener_usuario_por_id(db, usuario_id)
    if not usuario:
        raise ValueError("Usuario no encontrado")

    usuario.alias = nuevo_alias
    db.commit()
    return usuario
