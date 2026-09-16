"""Consultas do módulo de empresas."""

import uuid
from collections.abc import Iterable

from sqlalchemy import exists, select
from sqlalchemy.orm import Session

from app.modules.empresas.models import Empresa


def slug_em_uso(db: Session, slug: str) -> bool:
    return bool(db.scalar(select(exists().where(Empresa.slug == slug))))


def por_id(db: Session, empresa_id: uuid.UUID) -> Empresa | None:
    return db.get(Empresa, empresa_id)


def ativas_por_ids(db: Session, ids: Iterable[uuid.UUID]) -> list[Empresa]:
    ids = list(ids)
    if not ids:
        return []
    return list(db.scalars(select(Empresa).where(Empresa.id.in_(ids), Empresa.ativa.is_(True))))
