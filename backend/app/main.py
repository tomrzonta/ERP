"""Ponto de entrada da API."""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import settings
from app.core.exceptions import registrar_handlers
from app.modules.assinaturas.router import router as assinaturas_router
from app.modules.auth.router import router as auth_router
from app.modules.clientes.router import router as clientes_router
from app.modules.composicao.router import router as composicao_router
from app.modules.estoque.router import router as estoque_router
from app.modules.financeiro.router import router as financeiro_router
from app.modules.health.router import router as health_router
from app.modules.produtos.router import router as produtos_router
from app.modules.relatorios.router import router as relatorios_router
from app.modules.vendas.router import router as vendas_router

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
    app.include_router(auth_router, prefix=API_PREFIX)
    app.include_router(assinaturas_router, prefix=API_PREFIX)
    app.include_router(produtos_router, prefix=API_PREFIX)
    app.include_router(estoque_router, prefix=API_PREFIX)
    app.include_router(composicao_router, prefix=API_PREFIX)
    app.include_router(clientes_router, prefix=API_PREFIX)
    app.include_router(vendas_router, prefix=API_PREFIX)
    app.include_router(financeiro_router, prefix=API_PREFIX)
    app.include_router(relatorios_router, prefix=API_PREFIX)

    return app


app = create_app()
