"""Verifica se a API e o banco estão respondendo."""

import logging

from fastapi import APIRouter, Depends
from fastapi.responses import JSONResponse
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.database import get_db
from app.shared.seguranca import mascarar_segredos

router = APIRouter(tags=["health"])
logger = logging.getLogger("uvicorn.error")


@router.get("/health")
def health(db: Session = Depends(get_db)):
    try:
        db.execute(text("SELECT 1"))
        banco = "ok"
    except Exception as erro:
        # Nunca registrar a mensagem crua: ela pode conter a senha do banco
        logger.error(
            "Health check: banco indisponivel: %s: %s",
            type(erro).__name__,
            mascarar_segredos(str(erro)),
        )
        banco = "indisponivel"

    status_code = 200 if banco == "ok" else 503
    return JSONResponse(
        status_code=status_code,
        content={"api": "ok", "banco": banco, "ambiente": settings.environment},
    )
