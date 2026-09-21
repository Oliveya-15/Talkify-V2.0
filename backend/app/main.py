import logging

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings
from app.database import Base, engine
from app.models import *  # noqa: F401,F403 - ensures all models are registered before create_all

from app.api.routes import analytics, auth, chat, documents

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s [%(name)s] %(message)s",
)

app = FastAPI(
    title=settings.APP_NAME,
    description="AI-powered document intelligence and research assistant.",
    version="2.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
def on_startup():
    # For a student project, create_all is the pragmatic default for SQLite.
    # Once you switch to Postgres for real, Alembic migrations (backend/alembic/)
    # should own schema changes instead of create_all.
    Base.metadata.create_all(bind=engine)


@app.get("/api/health", tags=["health"])
def health():
    return {"status": "ok", "app": settings.APP_NAME}


app.include_router(auth.router)
app.include_router(documents.router)
app.include_router(chat.router)
app.include_router(analytics.router)
