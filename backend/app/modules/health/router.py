"""Verifica se a API e o banco estão respondendo."""

from fastapi import APIRouter, Depends
from fastapi.responses import JSONResponse
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.database import get_db

router = APIRouter(tags=["health"])


@router.get("/health")
def health(db: Session = Depends(get_db)):
    try:
        db.execute(text("SELECT 1"))
        banco = "ok"
    except Exception:
        banco = "indisponivel"

    status_code = 200 if banco == "ok" else 503
    return JSONResponse(
        status_code=status_code,
        content={"api": "ok", "banco": banco, "ambiente": settings.environment},
    )
