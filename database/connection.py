import os
from pathlib import Path
from sqlalchemy import create_engine, inspect, text
from sqlalchemy.orm import sessionmaker, DeclarativeBase

_DB_DIR = Path(__file__).resolve().parent.parent
DATABASE_PATH = os.getenv("DATABASE_PATH", str(_DB_DIR / "database.db"))
DATABASE_URL = f"sqlite:///{DATABASE_PATH}"

engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


class Base(DeclarativeBase):
    pass


def ensure_columns(tabla: str, columnas: dict[str, str]) -> None:
    """create_all() no agrega columnas a tablas que ya existen: las suma acá.

    `columnas` mapea nombre de columna -> sentencia DDL completa (constante del código,
    nunca datos del usuario). No se arma SQL por interpolación.
    """
    existentes = {c["name"] for c in inspect(engine).get_columns(tabla)}
    with engine.begin() as conn:
        for nombre, ddl in columnas.items():
            if nombre not in existentes:
                conn.execute(text(ddl))

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
