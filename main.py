from pathlib import Path
from dotenv import load_dotenv
from fastapi import FastAPI
from Back_Opecode.database.connection import engine, Base
from Back_Opecode.routes.auth import router as auth_router
from Back_Opecode.routes.usuarios import router as usuarios_router

load_dotenv(Path(__file__).parent / ".env")

Base.metadata.create_all(bind=engine)

app = FastAPI(title="Broker Simulador - Backend", version="2.0.0")

app.include_router(auth_router)
app.include_router(usuarios_router)


@app.get("/health")
def health():
    return {"status": "ok", "version": "2.0.0", "password_hashing": "argon2id"}
