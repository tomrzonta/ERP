"""Consultas do módulo de acesso."""

import uuid

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.modules.acesso.models import PapelPermissao


def codigos_do_papel(db: Session, papel_id: uuid.UUID) -> list[str]:
    return list(
        db.scalars(select(PapelPermissao.permissao).where(PapelPermissao.papel_id == papel_id))
    )
