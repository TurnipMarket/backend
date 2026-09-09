from pathlib import Path
from dotenv import load_dotenv
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from database.connection import engine, Base
from routes.auth import router as auth_router
from routes.usuarios import router as usuarios_router
from routes.productos import router as productos_router

load_dotenv(Path(__file__).parent / ".env")

Base.metadata.create_all(bind=engine)

app = FastAPI(title="Broker Simulador - Backend", version="2.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth_router)
app.include_router(usuarios_router)
app.include_router(productos_router)


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    body = exc.body.decode("utf-8") if isinstance(exc.body, bytes) else exc.body
    print(f"[VALIDATION ERROR] path={request.url.path} body_recibido={body}")
    print(f"[VALIDATION ERROR] errores={exc.errors()}")
    return JSONResponse(status_code=422, content={"detail": exc.errors()})


@app.get("/health")
def health():
    return {"status": "ok", "version": "2.0.0", "password_hashing": "argon2id"}