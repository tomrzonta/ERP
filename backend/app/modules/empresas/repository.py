"""Consultas do módulo de empresas."""

from sqlalchemy import exists, select
from sqlalchemy.orm import Session

from app.modules.empresas.models import Empresa


def slug_em_uso(db: Session, slug: str) -> bool:
    return bool(db.scalar(select(exists().where(Empresa.slug == slug))))
