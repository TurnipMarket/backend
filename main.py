from pathlib import Path
from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
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


@app.get("/health")
def health():
    return {"status": "ok", "version": "2.0.0", "password_hashing": "argon2id"}