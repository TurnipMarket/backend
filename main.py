from pathlib import Path
from dotenv import load_dotenv
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.encoders import jsonable_encoder
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
from database.connection import engine, Base, ensure_columns
from services.imagen_service import UPLOAD_DIR
from routes.auth import router as auth_router
from routes.usuarios import router as usuarios_router
from routes.productos import router as productos_router

load_dotenv(Path(__file__).parent / ".env")

Base.metadata.create_all(bind=engine)
ensure_columns("productos", {
    "categoria": "VARCHAR(30) NOT NULL DEFAULT 'other'",
    "moneda": "VARCHAR(3) NOT NULL DEFAULT 'ARS'",
    "condicion": "VARCHAR(20) NOT NULL DEFAULT 'new'",
    "estado": "VARCHAR(20) NOT NULL DEFAULT 'published'",
})
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)

app = FastAPI(title="Broker Simulador - Backend", version="2.0.0")

app.add_middleware(
    CORSMiddleware,
    # localhost y red local (192.168.x.x), con cualquier puerto.
    allow_origin_regex=r"https?://(localhost|127\.0\.0\.1|192\.168\.\d{1,3}\.\d{1,3})(:\d+)?$",
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.mount("/uploads", StaticFiles(directory=UPLOAD_DIR), name="uploads")

app.include_router(auth_router)
app.include_router(usuarios_router)
app.include_router(productos_router)


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    body = exc.body.decode("utf-8") if isinstance(exc.body, bytes) else exc.body
    # Se corta el body: puede traer una imagen en base64 de varios MB.
    print(f"[VALIDATION ERROR] path={request.url.path} body_recibido={str(body)[:300]}")
    print(f"[VALIDATION ERROR] errores={str(exc.errors())[:500]}")
    return JSONResponse(status_code=422, content={"detail": jsonable_encoder(exc.errors())})


@app.get("/health")
def health():
    return {"status": "ok", "version": "2.0.0", "password_hashing": "argon2id"}