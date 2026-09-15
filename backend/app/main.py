"""Ponto de entrada da API."""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import settings
from app.core.exceptions import registrar_handlers
from app.modules.health.router import router as health_router

API_PREFIX = "/api/v1"


def create_app() -> FastAPI:
    app = FastAPI(
        title=settings.app_name,
        # Documentação interativa desligada em produção
        docs_url=None if settings.is_production else "/docs",
        redoc_url=None,
    )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    registrar_handlers(app)

    # Registre aqui os routers de cada módulo
    app.include_router(health_router, prefix=API_PREFIX)

    return app


app = create_app()
